"""
Wordle statistics service.
Parses Wordle results from Discord messages and calculates statistics.
"""

import re
from typing import List, Dict
from collections import defaultdict
from app.models.discord import DiscordMessage, UserMessageStats
from app.models.wordle import WordleResult, WordleUserStats, WordleStats


class WordleService:
    """Service for parsing and analyzing Wordle results."""

    # Pattern to match results like "3/6: <@123456>" or "X/6: <@123456> <@789>"
    RESULT_PATTERN = re.compile(r'([X\d])/6:\s*(<@\d+>(?:\s*<@\d+>)*)')
    USER_MENTION_PATTERN = re.compile(r'<@(\d+)>')

    def parse_wordle_results(
        self, messages: List[DiscordMessage], user_stats: List[UserMessageStats]
    ) -> List[WordleResult]:
        """
        Parse Wordle results from Discord bot messages.

        Args:
            messages: List of Discord messages
            user_stats: List of user stats to map Discord IDs to usernames

        Returns:
            List of WordleResult objects
        """
        # Create mapping of Discord ID to username
        id_to_username = {str(stat.user_id): stat.username for stat in user_stats}

        results = []
        wordle_number = 0  # We don't track specific Wordle numbers from bot messages

        # Filter to Wordle bot messages
        wordle_bot_msgs = [m for m in messages if m.author_name.lower() == 'wordle']

        for msg in wordle_bot_msgs:
            for match in self.RESULT_PATTERN.finditer(msg.content):
                score = match.group(1)
                mentions_str = match.group(2)

                # Convert score to number (X = 7 for failure)
                if score.upper() == 'X':
                    guesses = 7
                    is_win = False
                else:
                    guesses = int(score)
                    is_win = True

                # Extract all user IDs from mentions
                user_ids = self.USER_MENTION_PATTERN.findall(mentions_str)

                for user_id in user_ids:
                    username = id_to_username.get(user_id, f"User_{user_id}")
                    results.append(
                        WordleResult(
                            author_name=username,
                            wordle_number=wordle_number,
                            guesses=guesses,
                            is_win=is_win,
                        )
                    )

        return results

    def calculate_stats(self, results: List[WordleResult]) -> WordleStats:
        """
        Calculate Wordle statistics from parsed results.

        Args:
            results: List of WordleResult objects

        Returns:
            WordleStats object with aggregated statistics
        """
        # Group results by user
        user_results = defaultdict(list)
        for result in results:
            user_results[result.author_name].append(result)

        # Calculate per-user stats
        user_stats = []
        for username, user_games in user_results.items():
            wins = [g for g in user_games if g.is_win]
            losses = [g for g in user_games if not g.is_win]

            total_games = len(user_games)
            win_count = len(wins)
            loss_count = len(losses)
            win_rate = (win_count / total_games * 100) if total_games > 0 else 0.0

            # Calculate average guesses for wins only
            avg_guesses = (sum(g.guesses for g in wins) / len(wins)) if wins else 0.0

            user_stats.append(
                WordleUserStats(
                    username=username,
                    total_games=total_games,
                    wins=win_count,
                    losses=loss_count,
                    win_rate=round(win_rate, 1),
                    average_guesses=round(avg_guesses, 2),
                )
            )

        return WordleStats(
            total_games=len(results),
            total_wins=sum(r.is_win for r in results),
            total_losses=sum(not r.is_win for r in results),
            user_stats=user_stats,
        )

    def get_top_winners(
        self, stats: WordleStats, limit: int = 5
    ) -> List[WordleUserStats]:
        """
        Get top users by win count and win rate.

        Args:
            stats: WordleStats object
            limit: Number of top users to return

        Returns:
            List of top WordleUserStats sorted by wins then win rate
        """
        # Filter users with at least 1 game
        qualified = [s for s in stats.user_stats if s.total_games > 0]

        # Sort by wins (descending), then by win rate (descending)
        sorted_stats = sorted(
            qualified,
            key=lambda x: (x.wins, x.win_rate),
            reverse=True
        )
        return sorted_stats[:limit]

    def get_top_failures(
        self, stats: WordleStats, limit: int = 5
    ) -> List[WordleUserStats]:
        """
        Get users with most Wordle failures.

        Args:
            stats: WordleStats object
            limit: Number of users to return

        Returns:
            List of WordleUserStats sorted by losses
        """
        # Filter users with at least 1 loss
        with_losses = [s for s in stats.user_stats if s.losses > 0]

        # Sort by losses (descending)
        sorted_stats = sorted(
            with_losses,
            key=lambda x: x.losses,
            reverse=True
        )
        return sorted_stats[:limit]

    def get_lowest_average(
        self, stats: WordleStats, limit: int = 5, min_games: int = 3
    ) -> List[WordleUserStats]:
        """
        Get users with lowest average guesses (best players).

        Args:
            stats: WordleStats object
            limit: Number of users to return
            min_games: Minimum games to qualify

        Returns:
            List of WordleUserStats sorted by average guesses (ascending)
        """
        # Filter users with enough games and at least 1 win
        qualified = [s for s in stats.user_stats if s.total_games >= min_games and s.wins > 0]

        # Sort by average guesses (ascending - lower is better)
        sorted_stats = sorted(
            qualified,
            key=lambda x: x.average_guesses
        )
        return sorted_stats[:limit]
