from math import ceil
from typing import Any, Generator
from unittest.mock import patch, Mock

import riva_api.proto.riva_tts_pb2 as rtts
import riva_api.proto.riva_tts_pb2_grpc as rtts_srv
from riva_api import AudioEncoding
from riva_api.tts import SpeechSynthesisService


TEXT = 'foo'
VOICE_NAME = "English-US-Female-1"
LANGUAGE_CODE = 'en-US'
ENCODING = AudioEncoding.LINEAR_PCM
SAMPLE_RATE_HZ = 44100
SAMPLE_WIDTH = 2
STREAMING_CHUNK_SIZE = 1000

AUDIO_BYTES_1_SECOND = b'a' * SAMPLE_WIDTH * SAMPLE_RATE_HZ


def response_generator(chunk_size: int = STREAMING_CHUNK_SIZE) -> Generator[rtts.SynthesizeSpeechResponse, None, None]:
    for i in range(0, len(AUDIO_BYTES_1_SECOND), chunk_size):
        yield rtts.SynthesizeSpeechResponse(audio=AUDIO_BYTES_1_SECOND[i * chunk_size : (i + 1) * chunk_size])


SYNTHESIZE_MOCK = Mock(
    return_value=rtts.SynthesizeSpeechResponse(audio=AUDIO_BYTES_1_SECOND)
)
SYNTHESIZE_ONLINE_MOCK = Mock(return_value=response_generator())


def riva_stub_init_patch(self, channel):
    self.Synthesize = SYNTHESIZE_MOCK
    self.SynthesizeOnline = SYNTHESIZE_ONLINE_MOCK


def is_iterable(obj: Any) -> bool:
    try:
        iter(obj)
    except TypeError:
        return False
    return True


@patch("riva_api.proto.riva_tts_pb2_grpc.RivaSpeechSynthesisStub.__init__", riva_stub_init_patch)
class TestSpeechSynthesisService:
    def test_synthesize(self) -> None:
        auth = Mock()
        get_auth_return_value = 'get_auth_return_value'
        auth.get_auth_metadata = Mock(return_value=get_auth_return_value)
        SYNTHESIZE_MOCK.reset_mock()
        service = SpeechSynthesisService(auth)
        resp = service.synthesize(TEXT, VOICE_NAME, LANGUAGE_CODE, ENCODING, SAMPLE_RATE_HZ)
        assert isinstance(resp, rtts.SynthesizeSpeechResponse)
        SYNTHESIZE_MOCK.assert_called_with(
            rtts.SynthesizeSpeechRequest(
                text=TEXT,
                voice_name=VOICE_NAME,
                language_code=LANGUAGE_CODE,
                encoding=ENCODING,
                sample_rate_hz=SAMPLE_RATE_HZ,
            ),
            metadata=get_auth_return_value,
        )

    def test_synthesize_online(self) -> None:
        auth = Mock()
        get_auth_return_value = 'get_auth_return_value'
        auth.get_auth_metadata = Mock(return_value=get_auth_return_value)
        SYNTHESIZE_ONLINE_MOCK.reset_mock()
        service = SpeechSynthesisService(auth)
        responses = service.synthesize_online(TEXT, VOICE_NAME, LANGUAGE_CODE, ENCODING, SAMPLE_RATE_HZ)
        assert is_iterable(responses)
        SYNTHESIZE_ONLINE_MOCK.assert_called_with(
            rtts.SynthesizeSpeechRequest(
                text=TEXT,
                voice_name=VOICE_NAME,
                language_code=LANGUAGE_CODE,
                encoding=ENCODING,
                sample_rate_hz=SAMPLE_RATE_HZ,
            ),
            metadata=get_auth_return_value,
        )
        count = 0
        for resp in responses:
            assert isinstance(resp, rtts.SynthesizeSpeechResponse)
            count += 1
        assert count == ceil(len(AUDIO_BYTES_1_SECOND) / STREAMING_CHUNK_SIZE)


