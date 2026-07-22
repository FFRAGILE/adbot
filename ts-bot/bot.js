const { TeamSpeak, QueryProtocol } = require("ts3-nodejs-library");

// =================== تنظیمات ربات ===================
const config = {
    host: "127.0.0.1",              // آدرس سرور تیم اسپیک شما
    serverport: 9987,               // پورت کلاینت (پیش‌فرض 9987)
    queryport: 10011,               // پورت کوئری (پیش‌فرض 10011)
    nickname: "TS_Bot",             // نام ربات
    
    isAdmin: true,                  // اگر ادمین است true، اگر گست است false
    username: "serveradmin",        // نام کاربری کوئری
    password: "YOUR_PASSWORD"       // رمز عبور کوئری (برای گست خالی بگذارید)
};
// ===================================================

async function startBot() {
    console.log("Connecting to TeamSpeak...");
    try {
        const connectionParams = {
            host: config.host,
            queryport: config.queryport,
            serverport: config.serverport,
            nickname: config.nickname,
            protocol: QueryProtocol.RAW
        };

        if (config.isAdmin) {
            connectionParams.username = config.username;
            connectionParams.password = config.password;
        }

        const teamspeak = await TeamSpeak.connect(connectionParams);
        console.log("-> Connected successfully!");

        // گوش دادن به ورود کاربران
        await teamspeak.registerEvent("server");
        teamspeak.on("clientconnect", async (event) => {
            const client = event.client;
            if (client.type === 1) return; // نادیده گرفتن ربات‌های دیگر
            console.log(`User connected: ${client.nickname}`);
            
            if (config.isAdmin) {
                await client.message(`سلام ${client.nickname}، به سرور خوش آمدید.`);
            }
        });

    } catch (error) {
        console.error("Connection Error:", error.message);
    }
}

startBot();
