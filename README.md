# Protobuf
Protobuf message declarations used for operating the rover over the network

To test: 
```bash
mkdir generated
protoc -I=. --python_out=generated *.proto
```

If the dart_gen.dart script fails, try using from `Networking/` directory:
```bash
protoc --dart_out=lib/src/generated -I Protobuf Protobuf/*.proto Protobuf/google/protobuf/timestamp.proto
```
