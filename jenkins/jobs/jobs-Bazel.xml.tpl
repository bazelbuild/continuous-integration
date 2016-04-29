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
<matrix-project plugin="{{ variables.JENKINS_PLUGIN_matrix_project }}">
  <actions/>
  <description>Run the full test suite of Bazel.&#xd;
&#xd;
To be run on head and for release branch/tags only</description>
  <keepDependencies>false</keepDependencies>
  <properties>
    <com.coravy.hudson.plugins.github.GithubProjectProperty plugin="{{ variables.JENKINS_PLUGIN_github }}">
      <projectUrl>{{ variables.GITHUB_URL }}</projectUrl>
    </com.coravy.hudson.plugins.github.GithubProjectProperty>
    <hudson.model.ParametersDefinitionProperty>
      <parameterDefinitions>
        <net.uaznia.lukanus.hudson.plugins.gitparameter.GitParameterDefinition plugin="{{ variables.JENKINS_PLUGIN_git_parameter }}">
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
  <scm class="hudson.plugins.git.GitSCM" plugin="{{ variables.JENKINS_PLUGIN_git }}">
    <configVersion>2</configVersion>
    <userRemoteConfigs>
      <hudson.plugins.git.UserRemoteConfig>
        <refspec>+refs/heads/*:refs/remotes/origin/* +refs/notes/*:refs/notes/*</refspec>
        <url>{{ variables.GITHUB_URL }}</url>
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
      <values>{% for v in variables.PLATFORMS.split("\n") %}<string>{{ v }}</string>{% endfor %}</values>
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
    <org.jenkinsci.plugins.conditionalbuildstep.singlestep.SingleConditionalBuilder plugin="{{ variables.JENKINS_PLUGIN_conditional_buildstep }}">
      <condition class="org.jenkins_ci.plugins.run_condition.core.ExpressionCondition" plugin="{{ variables.JENKINS_PLUGIN_run_condition }}">
        <expression>(darwin|linux|ubuntu).*</expression>
        <label>${PLATFORM_NAME}</label>
      </condition>
      <buildStep class="hudson.tasks.Shell">
        <command>#!/bin/bash

source scripts/ci/build.sh

export BUILD_BY=&quot;Jenkins&quot;
export BUILD_LOG=&quot;${BUILD_URL}&quot;
export GIT_REPOSITORY_URL=&quot;${GIT_URL}&quot;
export BAZEL_COMPILE_TARGET=&quot;compile,determinism&quot;

if [[ &quot;${NODE_LABELS}&quot; =~ &quot;no-release&quot; ]]; then
  bazel_build
else
  bazel_build output/ci
fi
</command>
      </buildStep>
      <runner class="org.jenkins_ci.plugins.run_condition.BuildStepRunner$Fail" plugin="{{ variables.JENKINS_PLUGIN_run_condition }}"/>
    </org.jenkinsci.plugins.conditionalbuildstep.singlestep.SingleConditionalBuilder>
    <org.jenkinsci.plugins.conditionalbuildstep.singlestep.SingleConditionalBuilder plugin="{{ variables.JENKINS_PLUGIN_conditional_buildstep }}">
      <condition class="org.jenkins_ci.plugins.run_condition.core.ExpressionCondition" plugin="{{ variables.JENKINS_PLUGIN_run_condition }}">
        <expression>windows.*</expression>
        <label>${PLATFORM_NAME}</label>
      </condition>
      <buildStep class="hudson.tasks.BatchFile">
        <command>scripts\ci\windows\compile_windows.bat</command>
      </buildStep>
      <runner class="org.jenkins_ci.plugins.run_condition.BuildStepRunner$Fail" plugin="{{ variables.JENKINS_PLUGIN_run_condition }}"/>
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
    <hudson.tasks.Mailer plugin="{{ variables.JENKINS_PLUGIN_mailer }}">
      <recipients>{{ variables.BAZEL_BUILD_RECIPIENT }}</recipients>
      <dontNotifyEveryUnstableBuild>false</dontNotifyEveryUnstableBuild>
      <sendToIndividuals>false</sendToIndividuals>
    </hudson.tasks.Mailer>
    <hudson.plugins.parameterizedtrigger.BuildTrigger plugin="{{ variables.JENKINS_PLUGIN_parameterized_trigger }}">
      <configs>
        <hudson.plugins.parameterizedtrigger.BuildTriggerConfig>
          <configs>
            <hudson.plugins.parameterizedtrigger.CurrentBuildParameters/>
          </configs>
          <projects>Bazel-Install-Trigger</projects>
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
