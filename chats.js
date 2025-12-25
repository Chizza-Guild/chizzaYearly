require("dotenv").config();
const { Client, GatewayIntentBits } = require("discord.js");

const client = new Client({
	intents: [GatewayIntentBits.Guilds, GatewayIntentBits.GuildMessages, GatewayIntentBits.MessageContent, GatewayIntentBits.GuildMembers],
});

const stats = {
	customEmojis: {},
	mentions: {},
	images: {},
	gifs: {},
	messagesPerDay: {},
};

client.once("ready", async () => {
	console.log(`Logged in as ${client.user.tag}`);
	console.log("Starting server analysis...\n");

	try {
		const guild = process.env.GUILD_ID ? client.guilds.cache.get(process.env.GUILD_ID) : client.guilds.cache.first();

		if (!guild) {
			console.error("Guild not found!");
			return;
		}

		console.log(`Analyzing server: ${guild.name}\n`);

		await guild.members.fetch();

		const channels = guild.channels.cache.filter(ch => ch.isTextBased() && ch.permissionsFor(guild.members.me).has("ViewChannel"));

		console.log(`Found ${channels.size} accessible channels\n`);

		for (const [channelId, channel] of channels) {
			console.log(`Analyzing #${channel.name}...`);
			await analyzeChannel(channel, guild);
		}

		displayResults(guild);

		console.log("\nAnalysis complete!");
	} catch (error) {
		console.error("Error during analysis:", error);
	}
});

async function analyzeChannel(channel, guild) {
	try {
		let lastMessageId;
		let messagesProcessed = 0;

		while (true) {
			const options = { limit: 100 };
			if (lastMessageId) options.before = lastMessageId;

			const messages = await channel.messages.fetch(options);
			if (messages.size === 0) break;

			messages.forEach(msg => {
				if (msg.author.bot) return;

				const userId = msg.author.id;
				const member = guild.members.cache.get(userId);
				if (!member) return;

				const joinDate = member.joinedAt;
				if (!stats.messagesPerDay[userId]) {
					stats.messagesPerDay[userId] = {
						username: msg.author.username,
						joinDate: joinDate,
						messages: {},
					};
				}

				const msgDate = msg.createdAt.toISOString().split("T")[0];
				stats.messagesPerDay[userId].messages[msgDate] = (stats.messagesPerDay[userId].messages[msgDate] || 0) + 1;

				const customEmojiRegex = /<a?:(\w+):(\d+)>/g;
				let match;
				while ((match = customEmojiRegex.exec(msg.content)) !== null) {
					const emojiId = match[2];
					const emojiName = match[1];
					if (!stats.customEmojis[emojiId]) {
						stats.customEmojis[emojiId] = { name: emojiName, users: {} };
					}
					stats.customEmojis[emojiId].users[userId] = (stats.customEmojis[emojiId].users[userId] || 0) + 1;
				}

				msg.mentions.users.forEach(mentionedUser => {
					if (!mentionedUser.bot) {
						stats.mentions[mentionedUser.id] = (stats.mentions[mentionedUser.id] || 0) + 1;
					}
				});

				const hasImage = msg.attachments.some(att => att.contentType?.startsWith("image/")) || /\.(jpg|jpeg|png|gif|webp)(\?|$)/i.test(msg.content);

				if (hasImage) {
					stats.images[userId] = (stats.images[userId] || 0) + 1;
				}

				const hasGif = msg.attachments.some(att => att.contentType === "image/gif") || /(tenor\.com|giphy\.com)/i.test(msg.content);

				if (hasGif) {
					stats.gifs[userId] = (stats.gifs[userId] || 0) + 1;
				}
			});

			messagesProcessed += messages.size;
			lastMessageId = messages.last().id;

			await new Promise(resolve => setTimeout(resolve, 1000));
		}

		console.log(`  Processed ${messagesProcessed} messages`);
	} catch (error) {
		console.error(`  Error in #${channel.name}:`, error.message);
	}
}

function displayResults(guild) {
	console.log("\n" + "=".repeat(60));
	console.log("📊 SERVER STATISTICS RESULTS");
	console.log("=".repeat(60) + "\n");

	console.log("🎭 TOP 3 CUSTOM EMOJI USERS (per emoji):");
	const emojiStats = [];
	for (const [emojiId, data] of Object.entries(stats.customEmojis)) {
		const topUsers = Object.entries(data.users)
			.map(([userId, count]) => {
				const member = guild.members.cache.get(userId);
				return { username: member?.user.username || "Unknown", count };
			})
			.sort((a, b) => b.count - a.count)
			.slice(0, 3);

		emojiStats.push({ emoji: data.name, topUsers });
	}

	emojiStats.slice(0, 5).forEach(({ emoji, topUsers }) => {
		console.log(`\n  :${emoji}:`);
		topUsers.forEach((user, i) => {
			console.log(`    ${i + 1}. ${user.username} - ${user.count} times`);
		});
	});

	console.log("\n\n📢 TOP 3 MOST PINGED MEMBERS:");
	const topMentions = Object.entries(stats.mentions)
		.map(([userId, count]) => {
			const member = guild.members.cache.get(userId);
			return { username: member?.user.username || "Unknown", count };
		})
		.sort((a, b) => b.count - a.count)
		.slice(0, 3);

	topMentions.forEach((user, i) => {
		console.log(`  ${i + 1}. ${user.username} - ${user.count} mentions`);
	});

	console.log("\n\n🖼️  TOP 3 IMAGE SHARERS:");
	const topImages = Object.entries(stats.images)
		.map(([userId, count]) => {
			const member = guild.members.cache.get(userId);
			return { username: member?.user.username || "Unknown", count };
		})
		.sort((a, b) => b.count - a.count)
		.slice(0, 3);

	topImages.forEach((user, i) => {
		console.log(`  ${i + 1}. ${user.username} - ${user.count} images`);
	});

	console.log("\n\n🎬 TOP 3 GIF USERS:");
	const topGifs = Object.entries(stats.gifs)
		.map(([userId, count]) => {
			const member = guild.members.cache.get(userId);
			return { username: member?.user.username || "Unknown", count };
		})
		.sort((a, b) => b.count - a.count)
		.slice(0, 3);

	topGifs.forEach((user, i) => {
		console.log(`  ${i + 1}. ${user.username} - ${user.count} GIFs`);
	});

	console.log("\n\n💬 TOP 3 MOST TALKATIVE (messages per day since joining):");
	const messagesPerDayRanking = Object.entries(stats.messagesPerDay)
		.map(([userId, data]) => {
			const totalMessages = Object.values(data.messages).reduce((a, b) => a + b, 0);
			const daysInServer = data.joinDate ? Math.max(1, Math.floor((Date.now() - data.joinDate.getTime()) / (1000 * 60 * 60 * 24))) : 1;
			const avgPerDay = (totalMessages / daysInServer).toFixed(2);

			return {
				username: data.username,
				totalMessages,
				daysInServer,
				avgPerDay: parseFloat(avgPerDay),
			};
		})
		.sort((a, b) => b.avgPerDay - a.avgPerDay)
		.slice(0, 3);

	messagesPerDayRanking.forEach((user, i) => {
		console.log(`  ${i + 1}. ${user.username}`);
		console.log(`     ${user.avgPerDay} messages/day (${user.totalMessages} total, ${user.daysInServer} days)`);
	});

	console.log("\n" + "=".repeat(60) + "\n");
}

client.login(process.env.DISCORD_TOKEN);
