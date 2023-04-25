import os
os.system("protoc --python_out=src/generated -I Protobuf Protobuf/*.proto")