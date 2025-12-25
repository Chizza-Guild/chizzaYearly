require("dotenv").config();
const { Client, GatewayIntentBits } = require("discord.js");

const client = new Client({
	intents: [GatewayIntentBits.Guilds, GatewayIntentBits.GuildMessages, GatewayIntentBits.MessageContent],
});

const CHANNEL_ID = process.env.WORDLE_CHANNEL_ID;
const stats = new Map(); // userId -> { wins: 0, failures: 0, totalTries: 0, gamesPlayed: 0 }
const usernameToId = new Map(); // username -> userId mapping

client.once("ready", async () => {
	console.log(`Logged in as ${client.user.tag}`);
	await analyzeWordleMessages();
});

async function analyzeWordleMessages() {
	try {
		const channel = await client.channels.fetch(CHANNEL_ID);
		if (!channel || !channel.isTextBased()) {
			console.error("Invalid channel or not a text channel");
			return;
		}

		console.log("Fetching messages...");
		let allMessages = [];
		let lastId;

		// Fetch all messages in batches of 100
		while (true) {
			const options = { limit: 100 };
			if (lastId) options.before = lastId;

			const messages = await channel.messages.fetch(options);
			if (messages.size === 0) break;

			allMessages.push(...messages.values());
			lastId = messages.last().id;
			console.log(`Fetched ${allMessages.length} messages so far...`);
		}

		console.log(`Total messages fetched: ${allMessages.length}`);

		// Parse wordle results
		let gamesProcessed = 0;
		for (const msg of allMessages) {
			if (msg.content.includes("day streak") && msg.content.includes("Here are yesterday's results:")) {
				parseWordleMessage(msg.content);
				gamesProcessed++;
			}
		}

		console.log(`Games processed: ${gamesProcessed}`);
		console.log(`Unique players: ${stats.size}`);
		displayStats();
		process.exit(0);
	} catch (error) {
		console.error("Error analyzing messages:", error);
		process.exit(1);
	}
}

function parseWordleMessage(content) {
	const dayResults = new Map(); // userId/username -> score for this day
	const lines = content.split("\n");

	// First pass: collect all scores for this day
	for (const line of lines) {
		// Match score pattern at start of line (with optional crown emoji)
		const scoreMatch = line.match(/^[👑\s]*([X\d])\/6:/);
		if (scoreMatch) {
			const score = scoreMatch[1];

			// Find all user IDs in this line
			const userIdMatches = [...line.matchAll(/<@(\d+)>/g)];

			// Find all @username mentions (without the < >)
			const usernameMatches = [...line.matchAll(/@([a-zA-Z0-9_]+)/g)];

			// Process user IDs
			for (const userMatch of userIdMatches) {
				const userId = userMatch[1];
				addUserScore(userId, score, dayResults);
			}

			// Process usernames
			for (const usernameMatch of usernameMatches) {
				const username = usernameMatch[1];
				// Use username as identifier (prefixed to distinguish from IDs)
				const identifier = `username_${username}`;
				addUserScore(identifier, score, dayResults);
			}
		}
	}

	// Second pass: determine winner(s) - person with lowest score
	if (dayResults.size > 0) {
		let lowestScore = Infinity;

		// Find the lowest score
		for (const score of dayResults.values()) {
			if (score < lowestScore) {
				lowestScore = score;
			}
		}

		// Award win to all users with the lowest score
		for (const [identifier, score] of dayResults.entries()) {
			if (score === lowestScore && score !== Infinity) {
				if (stats.has(identifier)) {
					stats.get(identifier).wins++;
				}
			}
		}
	}
}

function addUserScore(identifier, score, dayResults) {
	if (!stats.has(identifier)) {
		stats.set(identifier, { wins: 0, failures: 0, totalTries: 0, gamesPlayed: 0 });
	}

	const userStats = stats.get(identifier);
	userStats.gamesPlayed++;

	if (score === "X") {
		userStats.failures++;
		userStats.totalTries += 7; // Count X as 7 for average calculation
		dayResults.set(identifier, Infinity);
	} else {
		const tries = parseInt(score);
		userStats.totalTries += tries;
		dayResults.set(identifier, tries);
	}
}

function displayStats() {
	console.log("\n=== WORDLE STATISTICS ===\n");

	// Convert to array for sorting
	const statsArray = Array.from(stats.entries()).map(([identifier, data]) => ({
		identifier,
		displayName: identifier.startsWith("username_") ? `@${identifier.replace("username_", "")}` : `<@${identifier}>`,
		...data,
		average: data.gamesPlayed > 0 ? (data.totalTries / data.gamesPlayed).toFixed(2) : 0,
		winRate: data.gamesPlayed > 0 ? ((data.wins / data.gamesPlayed) * 100).toFixed(1) : 0,
		failRate: data.gamesPlayed > 0 ? ((data.failures / data.gamesPlayed) * 100).toFixed(1) : 0,
	}));

	// Most wins
	const mostWins = [...statsArray].sort((a, b) => b.wins - a.wins);
	console.log("🏆 MOST WINS:");
	mostWins.forEach((user, i) => {
		console.log(`${i + 1}. ${user.displayName}: ${user.wins} wins (${user.gamesPlayed} games, ${user.winRate}% win rate, avg: ${user.average})`);
	});

	// Most failures
	console.log("\n❌ MOST FAILURES:");
	const mostFailures = [...statsArray].sort((a, b) => b.failures - a.failures);
	mostFailures.forEach((user, i) => {
		console.log(`${i + 1}. ${user.displayName}: ${user.failures} failures (${user.gamesPlayed} games, ${user.failRate}% fail rate, avg: ${user.average})`);
	});

	// Best average
	console.log("\n⭐ BEST AVERAGE SCORE:");
	const bestAvg = [...statsArray]
		.filter(u => u.gamesPlayed >= 10) // Minimum 10 games
		.sort((a, b) => parseFloat(a.average) - parseFloat(b.average));
	bestAvg.forEach((user, i) => {
		console.log(`${i + 1}. ${user.displayName}: ${user.average} avg (${user.gamesPlayed} games, ${user.wins} wins, ${user.failures} failures)`);
	});

	// Best win rate
	console.log("\n🎯 BEST WIN RATE (min 10 games):");
	const bestWinRate = [...statsArray].filter(u => u.gamesPlayed >= 10).sort((a, b) => parseFloat(b.winRate) - parseFloat(a.winRate));
	bestWinRate.forEach((user, i) => {
		console.log(`${i + 1}. ${user.displayName}: ${user.winRate}% (${user.wins}/${user.gamesPlayed} games, avg: ${user.average})`);
	});

	console.log("\n=========================\n");
}

client.login(process.env.DISCORD_BOT_TOKEN);
