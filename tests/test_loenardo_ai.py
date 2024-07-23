import unittest
from unittest.mock import patch
from leonardo_ai import LeonardoAI, LeonardoAIError


class TestLeonardoAI(unittest.TestCase):

    def setUp(self):
        self.api_key = "test_api_key"
        self.leo = LeonardoAI(self.api_key)

    def test_initialization(self):
        self.assertEqual(self.leo.api_key, self.api_key)
        self.assertIsNotNone(self.leo.base_url)

    @patch('leonardo_ai.requests.post')
    def test_generate_images(self, mock_post):
        # Mock the API response
        mock_response = unittest.mock.Mock()
        mock_response.json.return_value = {
            "sdGenerationJob": {"generationId": "test_generation_id"}
        }
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        result = self.leo.generate_images("A test prompt")

        self.assertIn("generation_id", result)
        self.assertEqual(result["generation_id"], "test_generation_id")

    def test_invalid_api_key(self):
        with self.assertRaises(LeonardoAIError):
            LeonardoAI("")  # Empty API key should raise an error


if __name__ == '__main__':
    unittest.main()
