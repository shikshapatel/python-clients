# Copyright (c) 2020, NVIDIA CORPORATION. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#  * Neither the name of NVIDIA CORPORATION nor the names of its
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS ``AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY
# OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import argparse
import os
import sys
import wave

import grpc

import riva_api.proto.riva_asr_pb2 as rasr
import riva_api.proto.riva_asr_pb2_grpc as rasr_srv
import riva_api.proto.riva_audio_pb2 as ra
from riva_api.asr import ASR_Client
from riva_api.auth import Auth


def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Streaming transcription via Riva AI Services")
    parser.add_argument("--riva-uri", default="localhost:50051", type=str, help="URI to GRPC server endpoint")
    parser.add_argument("--audio-file", required=True, help="path to local file to stream")
    parser.add_argument(
        "--show-intermediate", action="store_true", help="show intermediate transcripts as they are available"
    )
    parser.add_argument("--language-code", default="en-US", type=str, help="Language code of the model to be used")
    parser.add_argument("--boosted_lm_words", type=str, action='append', help="Words to boost when decoding")
    parser.add_argument(
        "--boosted_lm_score", type=float, default=4.0, help="Value by which to boost words when decoding"
    )
    parser.add_argument("--ssl_cert", type=str, help="Path to SSL client certificatates file")
    parser.add_argument(
        "--use_ssl", default=False, action='store_true', help="Boolean to control if SSL/TLS encryption should be used"
    )
    parser.add_argument("--file_streaming_chunk", type=int, default=1600)
    return parser.parse_args()


def main() -> None:
    args = get_args()
    auth = Auth(args.ssl_cert, args.use_ssl, args.riva_uri)
    asr_client = ASR_Client(auth)
    config = rasr.StreamingRecognitionConfig(
        config=rasr.RecognitionConfig(
            encoding=ra.AudioEncoding.LINEAR_PCM, language_code=args.language_code, max_alternatives=1,
        ),
        interim_results=True,
    )
    asr_client.streaming_recognize_file_print(
        input_file=args.audio_file,
        streaming_config=config,
        simulate_realtime=False,
        output_file=sys.stdout,
        pretty_overwrite=True,
        boosted_lm_words=args.boosted_lm_words,
        boosted_lm_score=args.boosted_lm_score,
        file_streaming_chunk=args.file_streaming_chunk,
        prefix_for_transcripts='>> vs ##',
        show_intermediate=args.show_intermediate,
    )


if __name__ == "__main__":
    main()
