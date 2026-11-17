"""Tests for speech/tts.py (AWS Polly TTS pipeline)."""
import sys
import io
import pytest
from unittest.mock import MagicMock, patch, call

import speech.tts as tts_module


class TestTTSImport:
    def test_tts_importable(self):
        """speech.tts should import without crashing."""
        import speech.tts  # noqa: F401

    def test_polly_client_created(self):
        """The module-level polly client should be a boto3 client object."""
        assert tts_module.polly is not None


class TestSpeak:
    """Tests for the speak() function."""

    @pytest.fixture
    def mock_polly_response(self):
        """Standard mocked Polly response returning 100 bytes of silence PCM."""
        pcm_bytes = b"\x00" * 100
        mock_response = {
            "AudioStream": io.BytesIO(pcm_bytes)
        }
        return mock_response

    def test_normal_text_no_crash(self, mock_polly_response):
        """speak() should run without raising when Polly and PyAudio succeed."""
        mock_p = MagicMock()
        mock_stream = MagicMock()
        mock_p.open.return_value = mock_stream
        mock_p.get_format_from_width.return_value = 8  # paInt16

        with patch.object(tts_module.polly, "synthesize_speech", return_value=mock_polly_response), \
             patch("speech.tts.pyaudio.PyAudio", return_value=mock_p):
            # Should not raise
            tts_module.speak("Hello, this is a test.")
        mock_stream.write.assert_called_once()
        mock_stream.stop_stream.assert_called_once()
        mock_stream.close.assert_called_once()
        mock_p.terminate.assert_called_once()

    def test_default_voice_is_joanna(self, mock_polly_response):
        """Default voice_id should be 'Joanna'."""
        mock_p = MagicMock()
        with patch.object(tts_module.polly, "synthesize_speech", return_value=mock_polly_response) as mock_synth, \
             patch("speech.tts.pyaudio.PyAudio", return_value=mock_p):
            tts_module.speak("Test")
        call_kwargs = mock_synth.call_args[1]
        assert call_kwargs.get("VoiceId") == "Joanna"

    def test_default_engine_is_neural(self, mock_polly_response):
        """Default engine should be 'neural'."""
        mock_p = MagicMock()
        with patch.object(tts_module.polly, "synthesize_speech", return_value=mock_polly_response) as mock_synth, \
             patch("speech.tts.pyaudio.PyAudio", return_value=mock_p):
            tts_module.speak("Test")
        call_kwargs = mock_synth.call_args[1]
        assert call_kwargs.get("Engine") == "neural"

    def test_pcm_format_requested(self, mock_polly_response):
        """OutputFormat should be 'pcm' so it streams raw audio."""
        mock_p = MagicMock()
        with patch.object(tts_module.polly, "synthesize_speech", return_value=mock_polly_response) as mock_synth, \
             patch("speech.tts.pyaudio.PyAudio", return_value=mock_p):
            tts_module.speak("Test")
        call_kwargs = mock_synth.call_args[1]
        assert call_kwargs.get("OutputFormat") == "pcm"

    def test_empty_text_does_not_crash(self, mock_polly_response):
        """speak('') should not raise – edge case with empty string."""
        mock_p = MagicMock()
        with patch.object(tts_module.polly, "synthesize_speech", return_value=mock_polly_response), \
             patch("speech.tts.pyaudio.PyAudio", return_value=mock_p):
            tts_module.speak("")  # Should not raise

    def test_long_text_no_crash(self, mock_polly_response):
        """speak() with a very long string should not crash (mocked)."""
        long_text = "a " * 2000
        mock_p = MagicMock()
        with patch.object(tts_module.polly, "synthesize_speech", return_value=mock_polly_response), \
             patch("speech.tts.pyaudio.PyAudio", return_value=mock_p):
            tts_module.speak(long_text)  # Should not raise

    def test_polly_api_failure_does_not_crash(self):
        """When Polly raises an exception, speak() should catch it and not propagate."""
        from botocore.exceptions import BotoCoreError, ClientError
        with patch.object(tts_module.polly, "synthesize_speech",
                          side_effect=Exception("Polly API error")):
            # Must NOT raise – exception is printed, not propagated
            tts_module.speak("Test")

    def test_missing_credentials_does_not_crash(self):
        """Missing AWS credentials raise a ClientError; speak() should catch it."""
        from botocore.exceptions import NoCredentialsError
        with patch.object(tts_module.polly, "synthesize_speech",
                          side_effect=NoCredentialsError()):
            tts_module.speak("Test")  # Must not propagate

    def test_custom_voice_passed_through(self, mock_polly_response):
        """Voice override should be forwarded to Polly."""
        mock_p = MagicMock()
        with patch.object(tts_module.polly, "synthesize_speech", return_value=mock_polly_response) as mock_synth, \
             patch("speech.tts.pyaudio.PyAudio", return_value=mock_p):
            tts_module.speak("Test", voice_id="Matthew")
        call_kwargs = mock_synth.call_args[1]
        assert call_kwargs.get("VoiceId") == "Matthew"

    def test_tts_no_response_key_handled(self):
        """When Polly response has no AudioStream, speak() should not propagate KeyError."""
        with patch.object(tts_module.polly, "synthesize_speech", return_value={}):
            tts_module.speak("Test")  # Must not raise
