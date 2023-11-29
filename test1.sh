curl -X POST http://localhost:5000/register \
-H "Content-Type: application/json" \
-d '{"email": "user@example.com", "hashed_password": "userpassword"}'

response=$(curl -X POST http://localhost:5000/user \
-H "Content-Type: application/json" \
-d '{"email": "user@example.com", "hashed_password": "userpassword"}')

JWT_TOKEN=$(echo $response | jq -r '.access_token')

curl -X POST http://localhost:5000/user/edit_video \
-H "Authorization: Bearer $JWT_TOKEN" \
-H "Content-Type: application/json" \
-d '{"src_file_path": "./test.MP4", "start_time": "00:00:10", "end_time": "00:00:30"}'
