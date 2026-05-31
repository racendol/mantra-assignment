from judge.serializers import JudgeRequestSerializer


class TestJudgeSerializer:
    def test_valid_payload(self):
        serializer = JudgeRequestSerializer(
            data={
                "sentence1": "A",
                "sentence2": "B",
            }
        )

        assert serializer.is_valid()

    def test_missing_sentence1(self):
        serializer = JudgeRequestSerializer(
            data={
                "sentence2": "A",
            }
        )

        assert not serializer.is_valid()
        assert "sentence1" in serializer.errors

    def test_missing_sentence2(self):
        serializer = JudgeRequestSerializer(
            data={
                "sentence1": "A",
            }
        )

        assert not serializer.is_valid()
        assert "sentence2" in serializer.errors


class TestBulkJudgeSerializer:
    def test_valid_bulk_payload(self):
        serializer = JudgeRequestSerializer(
            data=[
                {
                    "sentence1": "A",
                    "sentence2": "B",
                },
                {
                    "sentence1": "C",
                    "sentence2": "D",
                },
            ],
            many=True,
        )

        assert serializer.is_valid()

    def test_bulk_limit_exceeded(self):
        payload = [
            {
                "sentence1": f"A{i}",
                "sentence2": f"B{i}",
            }
            for i in range(101)
        ]

        serializer = JudgeRequestSerializer(
            data=payload,
            many=True,
        )

        assert not serializer.is_valid()
