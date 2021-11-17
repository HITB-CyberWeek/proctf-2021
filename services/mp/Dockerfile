FROM mcr.microsoft.com/dotnet/sdk:5.0 AS publish
WORKDIR /app

COPY ./src/ /app/
RUN dotnet publish -c release -o ./out

FROM mcr.microsoft.com/dotnet/aspnet:5.0
WORKDIR /app

COPY --from=publish /app/out/ /app/

CMD ["dotnet", "mp.dll"]
