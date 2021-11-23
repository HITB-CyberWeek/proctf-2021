FROM mcr.microsoft.com/dotnet/sdk:5.0-bullseye-slim AS build
WORKDIR /src
COPY ["OAuthServer.csproj", ""]
RUN dotnet restore "./OAuthServer.csproj"
COPY . .
RUN dotnet build "OAuthServer.csproj" -c Release -o /app/build
RUN dotnet publish "OAuthServer.csproj" -c Release -o /app/publish

FROM mcr.microsoft.com/dotnet/aspnet:5.0-bullseye-slim
WORKDIR /app
COPY --from=build /app/publish .

COPY ./server.pfx .
ENV ASPNETCORE_Kestrel__Certificates__Default__Path "/app/server.pfx"

RUN mkdir -p /root/.aspnet/DataProtection-Keys
VOLUME /root/.aspnet/DataProtection-Keys

EXPOSE 5000

ENTRYPOINT ["dotnet", "OAuthServer.dll"]
