const fs = require(`fs`);
const path = require(`path`);
const express = require(`express`);
const expressWs = require('express-ws');
const bodyParser = require(`body-parser`);
const config = require(`config`);
const sqlite3 = require(`sqlite3-promisify`);
const twilio = require(`twilio`);
const MessagingResponse = require('twilio').twiml.MessagingResponse;
const sql = require(`./sql/sql`);
const app = express();
const port = 8080;

const activeSubscriber = {};
const defaultTopic = `test`;

let dbConn = null;
let sms = null;

expressWs(app);
// app.use(express.static('public'));
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

// API - test
app.get('/hi', (req, res) => {
	res.send('Hello World!');
});

// API - Register
app.post('/reg', async (req, res) => {
	try {
		console.log(`[reg] started`);
		const body = req.body;
		const ip = req.headers['x-forwarded-for'] || req.connection.remoteAddress;

		if (!body.src || !body.topic) {
			throw `request format invalid: ${JSON.stringify(body)}`;
		}

		console.log(`[reg] ip = ${ip}; topic = ${body.topic}`);
		const statement = sql.insertSubscriber(ip, body.src, new Date(), body.topic);
		await dbConn.run(statement);

		res.send({
			status: 0,
			msg: `ok`
		});
	} catch (e) {
		console.log(e);
		res.send({
			status: 500,
			error: JSON.stringify(e)
		});
	}
});

// API - twilio sms incoming
app.post(`/sms`, async (req, res) => {
	try {
		console.log(`[/sms] start`);

		const body = req.body;
		const fromNumber = body.From;
		const msg = body.Body;

		console.log(`[/sms] from = ${fromNumber}; msg = ${msg}`);

		const statement = sql.insertLog(fromNumber, new Date(), ``, ``, msg);
		await dbConn.run(statement);

		// forward message to dest subscriber
		if (activeSubscriber[defaultTopic]) {
			const validSubscriber = [];

			for (let i = 0; i < activeSubscriber[defaultTopic].length; i++) {
				const subscriber = activeSubscriber[defaultTopic][i].subscriber;
				const ws = activeSubscriber[defaultTopic][i].ws;

				try {
					ws.send(msg);
					validSubscriber.push(activeSubscriber[defaultTopic][i]);
				}
				catch (e) {
					console.log(`[/sms] error when pushing message to ${JSON.stringify(subscriber)}`);
				}
			}

			activeSubscriber[defaultTopic] = validSubscriber;
		}

		res.status(200);
		res.setHeader('Content-Type', 'text/xml');
		res.send(`<Response></Response>`);
	}
	catch (e) {
		console.log(e);
		res.status(200);
		res.setHeader('Content-Type', 'text/xml');
		res.send(`<Response></Response>`);
	}
});

// websocket
app.ws('/echo', (ws, req) => {
	try {
		const ip = req.headers['x-forwarded-for'] || req.connection.remoteAddress;
		ws.send(`hello there~`);

		ws.on('message', function (msg) {
			ws.send(`hello! ${msg}`);
		});
	} catch (e) {
		console.log(e);
	}
});

app.ws('/client', async (ws, req) => {
	try {
		const ip = req.headers['x-forwarded-for'] || req.connection.remoteAddress;
		console.log(`[/client] start; ip = ${ip}`);

		// query topic
		const row = await dbConn.get(sql.getLatestRegByIp(ip));

		if (activeSubscriber[row.topic]) {
			activeSubscriber[row.topic].push({
				subscriber: row,
				ws: ws
			});
		}
		else {
			activeSubscriber[row.topic] = [{
				subscriber: row,
				ws: ws
			}];
		}

		ws.on('message', function (msg) {
			ws.send(`hello! ${msg}`);
		});
	} catch (e) {
		console.log(e);
	}
});

// init
(async () => {
	try {
		// db
		const dbFile = path.resolve(__dirname, config.dbPath);

		if (!fs.existsSync(dbFile)) {
			fs.closeSync(fs.openSync(dbFile, 'w'));

			dbConn = new sqlite3(dbFile);
			await dbConn.run(sql.createTableSubscriber);
			await dbConn.run(sql.createTableLog);
		} else {
			dbConn = new sqlite3(dbFile);
		}

		// twilio
		const twilioSid = process.env.TSID;
		const twilioToken = process.env.TTOKEN;

		sms = twilio(twilioSid, twilioToken);

		console.log(`twilio env: sid = ${twilioSid.substring(0, 3)}...; token = ${twilioToken.substring(0, 3)}...`)

		// start server
		app.listen(port, () => {
			console.log(`server listening at http://localhost:${port}`);
		});
	} catch (e) {
		console.log(e);
	}
})();
