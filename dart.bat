@echo off
protoc --dart_out=generated -I Protobuf Protobuf/*.proto
