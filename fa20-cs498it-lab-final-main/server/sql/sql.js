const SqlString = require('sqlstring-sqlite');

module.exports.createTableSubscriber = `
CREATE TABLE subscriber (
	"_id" INTEGER PRIMARY KEY AUTOINCREMENT,
	ip TEXT,
	src TEXT,
	ts TEXT,
	topic TEXT
);
`;

module.exports.createTableLog = `
CREATE TABLE log (
	"_id" INTEGER PRIMARY KEY AUTOINCREMENT,
	caller TEXT,
	ts TEXT,
	topic TEXT,
	dest TEXT,
	msg TEXT
);
`;

module.exports.insertSubscriber = (ip, src, ts, topic) => `
INSERT INTO subscriber 
(ip, src, ts, topic) 
VALUES(${SqlString.escape(ip)}, ${SqlString.escape(src)}, ${SqlString.escape(ts)}, ${SqlString.escape(topic)});
`;

module.exports.insertLog = (caller, ts, topic, dest, msg) => `
INSERT INTO log
(caller, ts, topic, dest, msg)
VALUES(${SqlString.escape(caller)}, ${SqlString.escape(ts)}, ${SqlString.escape(topic)}, ${SqlString.escape(dest)}, ${SqlString.escape(msg)});
`;

module.exports.getLatestRegByIp = (ip) => `
select * from subscriber where ip=${SqlString.escape(ip)} order by _id desc limit 1;
`;
