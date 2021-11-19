FROM mcr.microsoft.com/dotnet/sdk:5.0-bullseye-slim AS publish
WORKDIR /app

COPY ./src/ /app/
RUN dotnet publish -c release -o ./out

FROM mcr.microsoft.com/dotnet/aspnet:5.0-bullseye-slim
WORKDIR /app

RUN apt-get update && apt-get install -y curl

COPY --from=publish /app/out/ /app/
COPY ./init-opensearch.sh .

CMD ["dotnet", "mp.dll"]
