


class TestScoreManager:
    def test_initialize_user_creates_record(self, test_score_manager):
        uid = test_score_manager.initialize_user()
        assert isinstance(uid, int)
        record = test_score_manager.get_user_score(uid)
        assert record['score'] == 0
        assert record['total_correct_answers'] == 0

    def test_initialize_user_with_existing_id(self, test_score_manager):
        uid = test_score_manager.initialize_user()
        uid2 = test_score_manager.initialize_user(user_id=uid)
        assert uid == uid2

    def test_initialize_user_with_mode_and_name(self, test_score_manager):
        uid = test_score_manager.initialize_user(mode='pixelation', player_name='Alice')
        record = test_score_manager.get_user_score(uid)
        assert record['mode'] == 'pixelation'
        assert record['player_name'] == 'Alice'

    def test_initialize_user_without_player_name(self, test_score_manager):
        uid = test_score_manager.initialize_user(mode='quiz')
        record = test_score_manager.get_user_score(uid)
        assert 'player_name' not in record

    def test_get_user_score_structure(self, test_score_manager):
        uid = test_score_manager.initialize_user()
        score = test_score_manager.get_user_score(uid)
        assert 'user_id' in score
        assert 'score' in score
        assert 'stats' in score
        assert 'total_correct_answers' in score

    def test_get_user_score_auto_initializes(self, test_score_manager):
        uid = 999_999_999
        score = test_score_manager.get_user_score(uid)
        assert score['user_id'] == uid
        assert score['score'] == 0

    def test_update_score_increment(self, test_score_manager):
        uid = test_score_manager.initialize_user()
        test_score_manager.update_score(uid, 1, stat_updates={'name': 1})
        score = test_score_manager.get_user_score(uid)
        assert score['score'] == 1
        assert score['total_correct_answers'] == 1

    def test_update_score_multiple_increments(self, test_score_manager):
        uid = test_score_manager.initialize_user()
        test_score_manager.update_score(uid, 1, stat_updates={'name': 1})
        test_score_manager.update_score(uid, 1, stat_updates={'company': 1})
        test_score_manager.update_score(uid, 1, stat_updates={'name': 1})
        score = test_score_manager.get_user_score(uid)
        assert score['score'] == 3
        assert score['total_correct_answers'] == 3

    def test_update_score_without_stats(self, test_score_manager):
        uid = test_score_manager.initialize_user()
        test_score_manager.update_score(uid, 2)
        score = test_score_manager.get_user_score(uid)
        assert score['score'] == 2

    def test_get_stats_returns_dict(self, test_score_manager):
        uid = test_score_manager.initialize_user()
        test_score_manager.update_score(uid, 1, stat_updates={'name': 1, 'company': 1})
        stats = test_score_manager.get_stats(uid)
        assert isinstance(stats, dict)
        assert stats['name'] == 1
        assert stats['company'] == 1

    def test_get_stats_empty_initially(self, test_score_manager):
        uid = test_score_manager.initialize_user()
        stats = test_score_manager.get_stats(uid)
        assert stats == {}

    def test_get_top_scores_with_mode(self, test_score_manager):
        uid1 = test_score_manager.initialize_user(mode='pixelation')
        uid2 = test_score_manager.initialize_user(mode='pixelation')
        uid3 = test_score_manager.initialize_user(mode='quiz')
        test_score_manager.update_score(uid1, 5)
        test_score_manager.update_score(uid2, 10)
        test_score_manager.update_score(uid3, 20)

        top = test_score_manager.get_top_scores(mode='pixelation')
        assert len(top) == 2
        assert top[0]['score'] >= top[1]['score']

    def test_get_top_scores_without_mode(self, test_score_manager):
        uid1 = test_score_manager.initialize_user(mode='pixelation')
        uid2 = test_score_manager.initialize_user(mode='quiz')
        test_score_manager.update_score(uid1, 5)
        test_score_manager.update_score(uid2, 10)

        top = test_score_manager.get_top_scores()
        assert len(top) == 2
        assert top[0]['score'] >= top[1]['score']

    def test_get_top_scores_respects_limit(self, test_score_manager):
        for _ in range(5):
            uid = test_score_manager.initialize_user()
            test_score_manager.update_score(uid, 1)
        top = test_score_manager.get_top_scores(limit=3)
        assert len(top) == 3

    def test_get_total_players(self, test_score_manager):
        assert test_score_manager.get_total_players() == 0
        test_score_manager.initialize_user()
        test_score_manager.initialize_user()
        assert test_score_manager.get_total_players() == 2

    def test_get_total_players_no_duplicates(self, test_score_manager):
        uid = test_score_manager.initialize_user()
        test_score_manager.initialize_user(user_id=uid)
        assert test_score_manager.get_total_players() == 1

    def test_get_average_score_empty(self, test_score_manager):
        assert test_score_manager.get_average_score() == 0.0

    def test_get_average_score(self, test_score_manager):
        uid1 = test_score_manager.initialize_user()
        uid2 = test_score_manager.initialize_user()
        test_score_manager.update_score(uid1, 10)
        test_score_manager.update_score(uid2, 20)
        assert test_score_manager.get_average_score() == 15.0

    def test_get_highest_score_empty(self, test_score_manager):
        assert test_score_manager.get_highest_score() == 0

    def test_get_highest_score(self, test_score_manager):
        uid1 = test_score_manager.initialize_user()
        uid2 = test_score_manager.initialize_user()
        test_score_manager.update_score(uid1, 5)
        test_score_manager.update_score(uid2, 15)
        assert test_score_manager.get_highest_score() == 15
