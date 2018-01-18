<?xml version='1.0' encoding='UTF-8'?>
<flow-definition plugin="workflow-job">
  <actions/>
  <description>Test Github pull requests for {{ variables.PROJECT_NAME }}.</description>
  <keepDependencies>false</keepDependencies>
  <properties>
    {% if variables.RUN_SEQUENTIAL == "true" %}
    <org.jenkinsci.plugins.workflow.job.properties.DisableConcurrentBuildsJobProperty/>
    {% endif %}
    <jenkins.model.BuildDiscarderProperty>
      <strategy class="hudson.tasks.LogRotator">
        <daysToKeep>90</daysToKeep>
        <numToKeep>-1</numToKeep>
        <artifactDaysToKeep>-1</artifactDaysToKeep>
        <artifactNumToKeep>-1</artifactNumToKeep>
      </strategy>
    </jenkins.model.BuildDiscarderProperty>
    <com.coravy.hudson.plugins.github.GithubProjectProperty>
      <projectUrl>{{ variables.GITHUB_URL }}</projectUrl>
    </com.coravy.hudson.plugins.github.GithubProjectProperty>
    <org.jenkinsci.plugins.workflow.job.properties.PipelineTriggersJobProperty>
      <triggers>
        <org.jenkinsci.plugins.ghprb.GhprbTrigger>
          <spec>H/5 * * * *</spec>
          <configVersion>3</configVersion>
          <adminlist></adminlist>
          <allowMembersOfWhitelistedOrgsAsAdmin>true</allowMembersOfWhitelistedOrgsAsAdmin>
          <orgslist>google bazelbuild abseil</orgslist>
          <cron>H/5 * * * *</cron>
          <buildDescTemplate></buildDescTemplate>
          <onlyTriggerPhrase>false</onlyTriggerPhrase>
          <useGitHubHooks>true</useGitHubHooks>
          <permitAll>false</permitAll>
          <whitelist></whitelist>
          <autoCloseFailedPullRequests>false</autoCloseFailedPullRequests>
          <displayBuildErrorsOnDownstreamBuilds>false</displayBuildErrorsOnDownstreamBuilds>
          <whiteListTargetBranches>
            <org.jenkinsci.plugins.ghprb.GhprbBranch>
              <branch></branch>
            </org.jenkinsci.plugins.ghprb.GhprbBranch>
          </whiteListTargetBranches>
          <blackListTargetBranches>
            <org.jenkinsci.plugins.ghprb.GhprbBranch>
              <branch></branch>
            </org.jenkinsci.plugins.ghprb.GhprbBranch>
          </blackListTargetBranches>
          <gitHubAuthId>58f0694f-1760-4610-b4f2-73ffb34c61a3</gitHubAuthId>
          <triggerPhrase></triggerPhrase>
          <skipBuildPhrase>.*\[skip\W+ci\].*</skipBuildPhrase>
          <blackListCommitAuthor></blackListCommitAuthor>
          <blackListLabels></blackListLabels>
          <whiteListLabels></whiteListLabels>
          <includedRegions></includedRegions>
          <excludedRegions></excludedRegions>
          <extensions>
            <org.jenkinsci.plugins.ghprb.extensions.status.GhprbSimpleStatus>
              <commitStatusContext>ci.bazel.build - {{ variables.NAME }}</commitStatusContext>
              <triggeredStatus></triggeredStatus>
              <startedStatus></startedStatus>
              <statusUrl>${RUN_DISPLAY_URL}</statusUrl>
              <addTestResults>false</addTestResults>
            </org.jenkinsci.plugins.ghprb.extensions.status.GhprbSimpleStatus>
          </extensions>
        </org.jenkinsci.plugins.ghprb.GhprbTrigger>
      </triggers>
    </org.jenkinsci.plugins.workflow.job.properties.PipelineTriggersJobProperty>
  </properties>
  <definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition" plugin="workflow-cps">
    <script><![CDATA[
    bazelCiConfiguredJob(
        repository: "{{ variables.GIT_URL }}",
        branch: env.sha1,
        refspec: "+refs/pull/*:refs/remotes/origin/pr/*",
        bazel_version: "latest",
        configuration: '''{{ raw_imports['JSON_CONFIGURATION'].replace('\\', '\\\\').replace("'", "\\'") }}''',
        workspace: "{{ variables.WORKSPACE }}",
        {% if variables.SAUCE_ENABLED == "true" %}
        sauce: "61b4846b-279d-4369-ae20-31e9d8b9bc66",
        {% endif %}
        run_sequentially: {{ variables.RUN_SEQUENTIAL }}
    )
    ]]></script>
    <sandbox>true</sandbox>
  </definition>
  <triggers/>
  <quietPeriod>5</quietPeriod>
  <disabled>{{ variables.disabled }}</disabled>
</flow-definition>
