FROM mcr.microsoft.com/dotnet/aspnet:10.0.12 AS scanner-runtime

FROM mcr.microsoft.com/dotnet/sdk:11.0.100-rc.1

LABEL "com.github.actions.name"="sonarscan-dotnet"
LABEL "com.github.actions.description"="SonarScanner for .NET 11 with pull request decoration support."
LABEL "com.github.actions.icon"="check-square"
LABEL "com.github.actions.color"="blue"

LABEL "org.opencontainers.image.source"="https://github.com/highbyte/sonarscan-dotnet"

LABEL "repository"="https://github.com/highbyte/sonarscan-dotnet"
LABEL "homepage"="https://github.com/highbyte"
LABEL "maintainer"="Highbyte"

# Version numbers of used software
ENV SONAR_SCANNER_DOTNET_TOOL_VERSION=11.3.0 \
    NODE_VERSION=24 \
    JRE_VERSION=21

# Fix JRE Install https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=863199
RUN mkdir -p /usr/share/man/man1

# Install a stable .NET runtime for SonarScanner alongside the prerelease SDK.
COPY --from=scanner-runtime /usr/share/dotnet/shared /usr/share/dotnet/shared

# Install NodeJS
RUN apt-get update -y \
    && apt-get install -y ca-certificates curl gnupg \
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_$NODE_VERSION.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list \
    && apt-get update -y \
    && apt-get install nodejs -y

# Install Java Runtime for SonarScanner
RUN apt-get install --no-install-recommends -y openjdk-$JRE_VERSION-jre

# Install SonarScanner .NET global tool
RUN dotnet tool install dotnet-sonarscanner --tool-path . --version $SONAR_SCANNER_DOTNET_TOOL_VERSION

# Cleanup
RUN apt-get -q -y autoremove \
    && apt-get -q clean -y \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*

COPY entrypoint.sh /entrypoint.sh

# Fix potential Windows line endings issue and ensure script is executable
RUN chmod +x /entrypoint.sh && \
    sed -i 's/\r$//' /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
