# ffmpeg-web-trim 

An python based backend application to trim videos from given period of time 

## feature 

- Operation record presists
- Async editing running 
- User authentication 
- Notification user when editing is done (using web push)

## Usage 

Start: 
```sh
git clone https://github.com/NoirJ0e/ffmpeg-web-trim.git
pip3 install -r requirements.txt
sh startup.sh
```

Create User:
```sh
curl -X POST http://localhost:5000/register \
-H "Content-Type: application/json" \
-d '{"email": "user@example.com", "hashed_password": "userpassword", "subscription_info": "None"}'
```

Login:
```sh
curl -X POST http://localhost:5000/user \
-H "Content-Type: application/json" \
-d '{"email": "user@example.com", "hashed_password": "userpassword"}'
```

Upload Video:
```sh
curl -X POST http://localhost:5000/user/edit_video \
-H "Authorization: Bearer $JWT_TOKEN \
-H "Content-Type: application/json" \
-d '{"src_file_path": "test.MP4", "start_time": "00:00:08", "end_time": "00:00:13"}'
```

Download Video:
```sh
curl -X GET "http://localhost:5000/user/download_video?operation_id=$operation_id" \
-H "Authorization: Bearer $JWT_TOKEN" \
-o $output_file
```

## WIP

- [ ] Editing progression track