# Azure-OpenAI-Service-Hackathon
Azure OpenAI Service Hackathon DataCampus Team


1. docker-compose build
2. docker-compose up
3. http://127.0.0.1:5000
    かなんか表示されるやつにアクセスしましょう

buildするとき
docker build -t my-flask-app .
docker run -p 5000:5000 -v $(pwd)/out:/app/out my-flask-app
ってやるとoutディレクトリがマウントされて画像保存されてる
でもここら辺の設定よくわからんわ
Dockerfileで記述できない????
