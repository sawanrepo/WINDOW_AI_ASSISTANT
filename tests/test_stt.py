"""Tests for speech/stt.py (Vosk STT pipeline)."""
import sys
import json
import pytest
from unittest.mock import MagicMock, patch, PropertyMock


class TestSTTImport:
    """Verify the STT module loads and the Vosk model is found on disk."""

    def test_stt_module_importable(self):
        """speech.stt should import without raising SystemExit when model is present."""
        import speech.stt  # noqa: F401

    def test_model_object_created(self):
        from speech.stt import model
        assert model is not None


class TestSTTListenErrorBranches:
    """Tests for error-handling paths in the listen() function."""

    def test_no_microphone_device_returns_mic_error(self):
        """When Microphone() raises, listen() returns 'Mic error.'"""
        import speech.stt as stt_module
        with patch("speech_recognition.Microphone", side_effect=Exception("No default audio device")):
            result = stt_module.listen()
        assert result == "Mic error."

    def test_wait_timeout_returns_didnt_hear(self):
        """When listen() times out (no speech), return 'Didn't hear anything.'"""
        import speech_recognition as sr
        import speech.stt as stt_module

        mock_source = MagicMock()
        mock_cm = MagicMock()
        mock_cm.__enter__ = MagicMock(return_value=mock_source)
        mock_cm.__exit__ = MagicMock(return_value=False)

        with patch("speech_recognition.Microphone", return_value=mock_cm), \
             patch.object(sr.Recognizer, "adjust_for_ambient_noise"), \
             patch.object(sr.Recognizer, "listen", side_effect=sr.WaitTimeoutError()):
            result = stt_module.listen()
        assert result == "Didn't hear anything."

    def test_empty_waveform_returns_didnt_catch(self):
        """When KaldiRecognizer returns empty text, return 'Didn't catch that clearly.'"""
        import speech_recognition as sr
        import speech.stt as stt_module

        mock_source = MagicMock()
        mock_cm = MagicMock()
        mock_cm.__enter__ = MagicMock(return_value=mock_source)
        mock_cm.__exit__ = MagicMock(return_value=False)

        # Create a fake audio object
        fake_audio = MagicMock(spec=sr.AudioData)
        fake_audio.get_raw_data.return_value = b"\x00" * 3200  # silence

        with patch("speech_recognition.Microphone", return_value=mock_cm), \
             patch.object(sr.Recognizer, "adjust_for_ambient_noise"), \
             patch.object(sr.Recognizer, "listen", return_value=fake_audio):
            # Patch KaldiRecognizer to return empty text
            with patch("speech.stt.KaldiRecognizer") as mock_rec_cls:
                mock_rec = MagicMock()
                mock_rec.AcceptWaveform.return_value = True
                mock_rec.Result.return_value = json.dumps({"text": ""})
                mock_rec_cls.return_value = mock_rec
                result = stt_module.listen()
        assert result == "Didn't catch that clearly."

    def test_valid_speech_returns_text(self):
        """When KaldiRecognizer returns a valid transcription, it is returned."""
        import speech_recognition as sr
        import speech.stt as stt_module

        mock_source = MagicMock()
        mock_cm = MagicMock()
        mock_cm.__enter__ = MagicMock(return_value=mock_source)
        mock_cm.__exit__ = MagicMock(return_value=False)
        fake_audio = MagicMock(spec=sr.AudioData)
        fake_audio.get_raw_data.return_value = b"\x01" * 3200

        with patch("speech_recognition.Microphone", return_value=mock_cm), \
             patch.object(sr.Recognizer, "adjust_for_ambient_noise"), \
             patch.object(sr.Recognizer, "listen", return_value=fake_audio):
            with patch("speech.stt.KaldiRecognizer") as mock_rec_cls:
                mock_rec = MagicMock()
                mock_rec.AcceptWaveform.return_value = True
                mock_rec.Result.return_value = json.dumps({"text": "open notepad"})
                mock_rec_cls.return_value = mock_rec
                result = stt_module.listen()
        assert result == "open notepad"

    def test_partial_result_fallback(self):
        """When AcceptWaveform is False, falls back to PartialResult."""
        import speech_recognition as sr
        import speech.stt as stt_module

        mock_source = MagicMock()
        mock_cm = MagicMock()
        mock_cm.__enter__ = MagicMock(return_value=mock_source)
        mock_cm.__exit__ = MagicMock(return_value=False)
        fake_audio = MagicMock(spec=sr.AudioData)
        fake_audio.get_raw_data.return_value = b"\x01" * 3200

        with patch("speech_recognition.Microphone", return_value=mock_cm), \
             patch.object(sr.Recognizer, "adjust_for_ambient_noise"), \
             patch.object(sr.Recognizer, "listen", return_value=fake_audio):
            with patch("speech.stt.KaldiRecognizer") as mock_rec_cls:
                mock_rec = MagicMock()
                mock_rec.AcceptWaveform.return_value = False
                mock_rec.PartialResult.return_value = json.dumps({"partial": "take screenshot"})
                mock_rec_cls.return_value = mock_rec
                result = stt_module.listen()
        assert result == "take screenshot"

    def test_stt_error_during_recognition(self):
        """When an exception occurs during recognition, return 'Error recognizing speech.'"""
        import speech_recognition as sr
        import speech.stt as stt_module

        mock_source = MagicMock()
        mock_cm = MagicMock()
        mock_cm.__enter__ = MagicMock(return_value=mock_source)
        mock_cm.__exit__ = MagicMock(return_value=False)
        fake_audio = MagicMock(spec=sr.AudioData)
        fake_audio.get_raw_data.return_value = b"\x01" * 3200

        with patch("speech_recognition.Microphone", return_value=mock_cm), \
             patch.object(sr.Recognizer, "adjust_for_ambient_noise"), \
             patch.object(sr.Recognizer, "listen", return_value=fake_audio):
            with patch("speech.stt.KaldiRecognizer", side_effect=RuntimeError("Model load failed")):
                result = stt_module.listen()
        assert result == "Error recognizing speech."
