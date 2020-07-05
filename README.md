# SonarScanner for .NET Core
SonarScanner for .NET Core for use in Github Actions, with automatic PR detection, analysis and decoration.

# Usage examples

## Simple use

``` yaml
    - name: SonarScanner for .NET Core with pull request decoration support
      uses: highbyte/sonarscan-dotnet
      with:
        # The key of the SonarQube project
        sonarProjectKey: your_projectkey
        # The name of the SonarQube project
        sonarProjectName:  your_projectname
        # The name of the SonarQube Organization
        sonarOrganization: your_organization

  env:
    SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

## Include code coverage with [Coverlet](https://github.com/coverlet-coverage/coverlet)
Also includes test results.

``` yaml
    - name: SonarScanner for .NET Core with pull request decoration support
      uses: highbyte/sonarscan-dotnet
      with:
        # The key of the SonarQube project
        sonarProjectKey: your_projectkey
        # The name of the SonarQube project
        sonarProjectName:  your_projectname
        # The name of the SonarQube Organization
        sonarOrganization: your_organization
        # Optional command arguments to dotnet test
        dotnetTestArguments: --logger trx --collect:"XPlat Code Coverage" -- DataCollectionRunSettings.DataCollectors.DataCollector.Configuration.Format=opencover
        # Optional extra command arguments the the SonarScanner 'begin' command
        sonarBeginArguments: /d:sonar.cs.opencover.reportsPaths="**/TestResults/**/coverage.opencover.xml" -d:sonar.cs.vstest.reportsPaths="**/TestResults/*.trx"
        
  env:
    SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

## Build subfolder src, and include code coverage
Also includes test results.

``` yaml
    - name: SonarScanner for .NET Core with pull request decoration support
      uses: highbyte/sonarscan-dotnet
      with:
        # The key of the SonarQube project
        sonarProjectKey: your_projectkey
        # The name of the SonarQube project
        sonarProjectName:  your_projectname
        # The name of the SonarQube Organization
        sonarOrganization: your_organization
        # Optional command arguments to dotnet dbuild
        dotnetTestArguments: ./src
        # Optional command arguments to dotnet test
        dotnetTestArguments: ./src --logger trx --collect:"XPlat Code Coverage" -- DataCollectionRunSettings.DataCollectors.DataCollector.Configuration.Format=opencover
        # Optional extra command arguments the the SonarScanner 'begin' command
        sonarBeginArguments: /d:sonar.cs.opencover.reportsPaths="**/TestResults/**/coverage.opencover.xml" -d:sonar.cs.vstest.reportsPaths="**/TestResults/*.trx"
        
  env:
    SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

# Secrets
- `SONAR_TOKEN` – **Required** this is the token used to authenticate access to SonarCloud. You can generate a token on your [Security page in SonarCloud](https://sonarcloud.io/account/security/). You can set the `SONAR_TOKEN` environment variable in the "Secrets" settings page of your repository.
- *`GITHUB_TOKEN` – Provided by Github (see [Authenticating with the GITHUB_TOKEN](https://help.github.com/en/actions/automating-your-workflow-with-github-actions/authenticating-with-the-github_token)).*


# Description of all inputs

``` yaml
inputs:
  sonarProjectKey:
    description: "The key of the SonarQube project"
    required: true
  sonarProjectName:
    description: "The name of the SonarQube project"
    required: true
  sonarOrganization:
    description: "The name of the SonarQube organization"
    required: true
  dotnetBuildArguments:
    description: "Optional command arguments to dotnet build"
    required: false
  dotnetTestArguments:
    description: "Optional command arguments to dotnet test"
    required: false
  sonarBeginArguments:
    description: "Optional extra command arguments the the SonarScanner 'begin' command"
    required: false
  sonarHostname:
    description: "The SonarQube server URL. For SonarCloud, leave this setting undefined"
    default: "https://sonarcloud.io"
    required: false
```

