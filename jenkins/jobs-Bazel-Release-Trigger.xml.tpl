<?xml version='1.0' encoding='UTF-8'?>
<project>
  <actions/>
  <description>This is just a job for sorting out wether a release should be triggered or not.</description>
  <logRotator class="hudson.tasks.LogRotator">
    <daysToKeep>-1</daysToKeep>
    <numToKeep>3</numToKeep>
    <artifactDaysToKeep>-1</artifactDaysToKeep>
    <artifactNumToKeep>-1</artifactNumToKeep>
  </logRotator>
  <keepDependencies>false</keepDependencies>
  <properties>
    <com.coravy.hudson.plugins.github.GithubProjectProperty plugin="%{JENKINS_PLUGIN_github}">
      <projectUrl>%{GITHUB_URL}</projectUrl>
    </com.coravy.hudson.plugins.github.GithubProjectProperty>
    <hudson.model.ParametersDefinitionProperty>
      <parameterDefinitions>
        <net.uaznia.lukanus.hudson.plugins.gitparameter.GitParameterDefinition plugin="%{JENKINS_PLUGIN_git-parameter}">
          <name>REF_SPEC</name>
          <description></description>
          <uuid>74b36fe4-c0a5-4a58-b8e4-d6b52b5c6909</uuid>
          <type>PT_BRANCH_TAG</type>
          <branch></branch>
          <tagFilter>*</tagFilter>
          <sortMode>NONE</sortMode>
          <defaultValue></defaultValue>
        </net.uaznia.lukanus.hudson.plugins.gitparameter.GitParameterDefinition>
      </parameterDefinitions>
    </hudson.model.ParametersDefinitionProperty>
  </properties>
  <scm class="hudson.plugins.git.GitSCM" plugin="%{JENKINS_PLUGIN_git}">
    <configVersion>2</configVersion>
    <userRemoteConfigs>
      <hudson.plugins.git.UserRemoteConfig>
        <refspec>+refs/heads/*:refs/remotes/origin/* +refs/notes/*:refs/notes/*</refspec>
        <url>%{GITHUB_URL}</url>
      </hudson.plugins.git.UserRemoteConfig>
    </userRemoteConfigs>
    <branches>
      <hudson.plugins.git.BranchSpec>
        <name>${REF_SPEC}</name>
      </hudson.plugins.git.BranchSpec>
    </branches>
    <doGenerateSubmoduleConfigurations>false</doGenerateSubmoduleConfigurations>
    <submoduleCfg class="list"/>
    <extensions/>
  </scm>
  <quietPeriod>5</quietPeriod>
  <assignedNode>deploy</assignedNode>
  <canRoam>false</canRoam>
  <disabled>false</disabled>
  <blockBuildWhenDownstreamBuilding>false</blockBuildWhenDownstreamBuilding>
  <blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>
  <triggers>
    <jenkins.triggers.ReverseBuildTrigger>
      <spec></spec>
      <upstreamProjects>Bazel, </upstreamProjects>
      <threshold>
        <name>SUCCESS</name>
        <ordinal>0</ordinal>
        <color>BLUE</color>
        <completeBuild>true</completeBuild>
      </threshold>
    </jenkins.triggers.ReverseBuildTrigger>
  </triggers>
  <concurrentBuild>false</concurrentBuild>
  <builders>
    <org.jenkinsci.plugins.conditionalbuildstep.singlestep.SingleConditionalBuilder plugin="%{JENKINS_PLUGIN_conditional-buildstep}">
      <condition class="org.jenkins_ci.plugins.run_condition.contributed.ShellCondition" plugin="%{JENKINS_PLUGIN_run-condition}">
        <command>#!/bin/bash

source scripts/release/common.sh

[ -n &quot;$(get_release_name)&quot; ]</command>
      </condition>
      <buildStep class="hudson.plugins.parameterizedtrigger.TriggerBuilder" plugin="%{JENKINS_PLUGIN_parameterized-trigger}">
        <configs>
          <hudson.plugins.parameterizedtrigger.BlockableBuildTriggerConfig>
            <configs>
              <hudson.plugins.parameterizedtrigger.CurrentBuildParameters/>
            </configs>
            <projects>Bazel-Release</projects>
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
