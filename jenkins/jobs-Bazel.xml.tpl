<?xml version='1.0' encoding='UTF-8'?>
<!--
  Copyright 2015 The Bazel Authors. All rights reserved.
 
  Licensed under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at
 
     http://www.apache.org/licenses/LICENSE-2.0
 
  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.
-->
<matrix-project plugin="%{JENKINS_PLUGIN_matrix-project}">
  <actions/>
  <description>Run the full test suite of Bazel.&#xd;
&#xd;
To be run on head and for release branch/tags only</description>
  <keepDependencies>false</keepDependencies>
  <properties>
    <com.coravy.hudson.plugins.github.GithubProjectProperty plugin="%{JENKINS_PLUGIN_github}">
      <projectUrl>%{GITHUB_URL}</projectUrl>
    </com.coravy.hudson.plugins.github.GithubProjectProperty>
    <hudson.model.ParametersDefinitionProperty>
      <parameterDefinitions>
        <net.uaznia.lukanus.hudson.plugins.gitparameter.GitParameterDefinition plugin="%{JENKINS_PLUGIN_git-parameter}">
          <name>REF_SPEC</name>
          <description>The branch / tag to build</description>
          <uuid>1ba7864c-b4fb-44b4-8268-31b304798afa</uuid>
          <type>PT_BRANCH_TAG</type>
          <branch></branch>
          <tagFilter>*</tagFilter>
          <sortMode>NONE</sortMode>
          <defaultValue>origin/master</defaultValue>
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
    <extensions>
      <hudson.plugins.git.extensions.impl.CleanBeforeCheckout/>
      <hudson.plugins.git.extensions.impl.AuthorInChangelog/>
    </extensions>
  </scm>
  <assignedNode>deploy</assignedNode>
  <canRoam>true</canRoam>
  <disabled>false</disabled>
  <blockBuildWhenDownstreamBuilding>false</blockBuildWhenDownstreamBuilding>
  <blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>
  <concurrentBuild>false</concurrentBuild>
  <axes>
    <hudson.matrix.LabelAxis>
      <name>PLATFORM_NAME</name>
      <values>%{PLATFORMS}</values>
    </hudson.matrix.LabelAxis>
    <hudson.matrix.TextAxis>
      <name>JAVA_VERSION</name>
      <values>
        <string>1.7</string>
        <string>1.8</string>
      </values>
    </hudson.matrix.TextAxis>
  </axes>
  <builders>
    <hudson.tasks.Shell>
      <command>#!/bin/bash

source scripts/ci/build.sh

export BUILD_BY=&quot;Jenkins&quot;
export BUILD_LOG=&quot;${BUILD_URL}&quot;
export GIT_REPOSITORY_URL=&quot;${GIT_URL}&quot;

if [[ &quot;${NODE_LABELS}&quot; =~ &quot;no-release&quot; ]]; then
  bazel_build
else
  bazel_build output/ci
fi
[ -z &quot;${BUILD_UNSTABLE-}&quot; ] || echo 1 &gt;unstable</command>
    </hudson.tasks.Shell>
    <org.jenkinsci.plugins.conditionalbuildstep.singlestep.SingleConditionalBuilder plugin="%{JENKINS_PLUGIN_conditional-buildstep}">
      <condition class="org.jenkins_ci.plugins.run_condition.core.FileExistsCondition" plugin="%{JENKINS_PLUGIN_run-condition}">
        <file>unstable</file>
        <baseDir class="org.jenkins_ci.plugins.run_condition.common.BaseDirectory$Workspace"/>
      </condition>
      <buildStep class="org.jenkins_ci.plugins.fail_the_build.FixResultBuilder" plugin="%{JENKINS_PLUGIN_fail-the-build-plugin}">
        <defaultResultName>UNSTABLE</defaultResultName>
        <success></success>
        <unstable></unstable>
        <failure></failure>
        <aborted></aborted>
      </buildStep>
      <runner class="org.jenkins_ci.plugins.run_condition.BuildStepRunner$Unstable" plugin="%{JENKINS_PLUGIN_run-condition}"/>
    </org.jenkinsci.plugins.conditionalbuildstep.singlestep.SingleConditionalBuilder>
  </builders>
  <publishers>
    <hudson.tasks.ArtifactArchiver>
      <artifacts>output/ci/**</artifacts>
      <allowEmptyArchive>true</allowEmptyArchive>
      <onlyIfSuccessful>false</onlyIfSuccessful>
      <fingerprint>false</fingerprint>
      <defaultExcludes>true</defaultExcludes>
    </hudson.tasks.ArtifactArchiver>
    <hudson.tasks.Mailer plugin="%{JENKINS_PLUGIN_mailer}">
      <recipients>%{BAZEL_BUILD_RECIPIENT}</recipients>
      <dontNotifyEveryUnstableBuild>false</dontNotifyEveryUnstableBuild>
      <sendToIndividuals>false</sendToIndividuals>
    </hudson.tasks.Mailer>
    <hudson.plugins.parameterizedtrigger.BuildTrigger plugin="%{JENKINS_PLUGIN_parameterized-trigger}">
      <configs>
        <hudson.plugins.parameterizedtrigger.BuildTriggerConfig>
          <configs>
            <hudson.plugins.parameterizedtrigger.CurrentBuildParameters/>
          </configs>
          <projects>Tutorial, %{BAZEL_JOBS}</projects>
          <condition>UNSTABLE_OR_BETTER</condition>
          <triggerWithNoParameters>false</triggerWithNoParameters>
        </hudson.plugins.parameterizedtrigger.BuildTriggerConfig>
      </configs>
    </hudson.plugins.parameterizedtrigger.BuildTrigger>
  </publishers>
  <buildWrappers/>
  <executionStrategy class="hudson.matrix.DefaultMatrixExecutionStrategyImpl">
    <runSequentially>false</runSequentially>
  </executionStrategy>
</matrix-project>
