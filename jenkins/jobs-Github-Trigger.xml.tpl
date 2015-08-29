<?xml version='1.0' encoding='UTF-8'?>
<project>
  <actions/>
  <description>The GitHub plugin doesn&apos;t work with tags and it&apos;s not really easy with it to have a job that you can trigger manually and when pushed to GitHub. This job fill the gaps by parsing itself the payload sent by the GitHub web hook.</description>
  <logRotator class="hudson.tasks.LogRotator">
    <daysToKeep>-1</daysToKeep>
    <numToKeep>10</numToKeep>
    <artifactDaysToKeep>-1</artifactDaysToKeep>
    <artifactNumToKeep>-1</artifactNumToKeep>
  </logRotator>
  <keepDependencies>false</keepDependencies>
  <properties>
    <hudson.model.ParametersDefinitionProperty>
      <parameterDefinitions>
        <hudson.model.StringParameterDefinition>
          <name>payload</name>
          <description>Payload sent by GitHub</description>
          <defaultValue>{}</defaultValue>
        </hudson.model.StringParameterDefinition>
      </parameterDefinitions>
    </hudson.model.ParametersDefinitionProperty>
  </properties>
  <scm class="hudson.scm.NullSCM"/>
  <assignedNode>deploy</assignedNode>
  <canRoam>false</canRoam>
  <disabled>false</disabled>
  <blockBuildWhenDownstreamBuilding>false</blockBuildWhenDownstreamBuilding>
  <blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>
  <authToken>##SECRET:github_trigger_auth_token##</authToken>
  <triggers/>
  <concurrentBuild>false</concurrentBuild>
  <builders>
    <org.jenkinsci.plugins.conditionalbuildstep.singlestep.SingleConditionalBuilder plugin="%{JENKINS_PLUGIN_conditional-buildstep}">
      <condition class="org.jenkins_ci.plugins.run_condition.contributed.ShellCondition" plugin="%{JENKINS_PLUGIN_run-condition}">
        <command>#!/bin/bash

# We should use jq, but installing it just for that is a bit overkill, we use regexp instead.
function extract_value() {
  echo &quot;$payload&quot; | grep -oE  &apos;&quot;&apos;$1&apos;&quot;\s*:\s*&quot;[^&quot;]*&quot;&apos; | sed -E &apos;s/^&quot;&apos;$1&apos;&quot;\s*:\s*&quot;(.*)&quot;$/\1/&apos;
}

export repository=$(extract_value full_name)
export ref=$(extract_value ref)
echo &quot;Got push to $repository on ref $ref&quot;

# Execute &apos;Bazel&apos; for master branch, releases branches and tags
if [ &quot;$repository&quot; = &quot;%{GITHUB_PROJECT}&quot; ]; then
  echo &quot;REF_SPEC=$ref&quot;&gt;REF_SPEC
  [ &quot;$ref&quot; = refs/heads/master ] &amp;&amp; exit 0
  [[ &quot;$ref&quot; =~ ^refs/heads/release-.*$ ]] &amp;&amp; exit 0
  [[ &quot;$ref&quot; =~ ^refs/tags/.*$ ]] &amp;&amp; exit 0
fi
exit 1</command>
      </condition>
      <buildStep class="hudson.plugins.parameterizedtrigger.TriggerBuilder" plugin="%{JENKINS_PLUGIN_parameterized-trigge">
        <configs>
          <hudson.plugins.parameterizedtrigger.BlockableBuildTriggerConfig>
            <configs>
              <hudson.plugins.parameterizedtrigger.FileBuildParameters>
                <propertiesFile>REF_SPEC</propertiesFile>
                <failTriggerOnMissing>true</failTriggerOnMissing>
                <useMatrixChild>false</useMatrixChild>
                <onlyExactRuns>false</onlyExactRuns>
              </hudson.plugins.parameterizedtrigger.FileBuildParameters>
            </configs>
            <projects>Bazel</projects>
            <condition>ALWAYS</condition>
            <triggerWithNoParameters>false</triggerWithNoParameters>
            <buildAllNodesWithLabel>false</buildAllNodesWithLabel>
          </hudson.plugins.parameterizedtrigger.BlockableBuildTriggerConfig>
        </configs>
      </buildStep>
      <runner class="org.jenkins_ci.plugins.run_condition.BuildStepRunner$Fail" plugin="%{JENKINS_PLUGIN_run-condition}"/>
    </org.jenkinsci.plugins.conditionalbuildstep.singlestep.SingleConditionalBuilder>
  </builders>
  <publishers/>
  <buildWrappers/>
</project>
