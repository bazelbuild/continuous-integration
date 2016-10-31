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
<project>
  <actions/>
  <description>Do the Github release of a Bazel binary</description>
  <keepDependencies>false</keepDependencies>
  <properties>
    <com.coravy.hudson.plugins.github.GithubProjectProperty plugin="{{ variables.JENKINS_PLUGIN_github }}">
      <projectUrl>{{ variables.GITHUB_URL }}</projectUrl>
    </com.coravy.hudson.plugins.github.GithubProjectProperty>
    <hudson.model.ParametersDefinitionProperty>
      <parameterDefinitions>
        <net.uaznia.lukanus.hudson.plugins.gitparameter.GitParameterDefinition plugin="{{ variables.JENKINS_PLUGIN_git_parameter }}">
          <name>REF_SPEC</name>
          <description></description>
          <uuid>ca709303-ae93-4be2-b9b8-5ab0c19672d1</uuid>
          <type>PT_BRANCH_TAG</type>
          <branch></branch>
          <tagFilter>*</tagFilter>
          <sortMode>NONE</sortMode>
          <defaultValue></defaultValue>
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
  <quietPeriod>5</quietPeriod>
  <assignedNode>deploy</assignedNode>
  <canRoam>false</canRoam>
  <disabled>false</disabled>
  <blockBuildWhenDownstreamBuilding>false</blockBuildWhenDownstreamBuilding>
  <blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>
  <triggers/>
  <concurrentBuild>false</concurrentBuild>
  <builders>
    <hudson.plugins.copyartifact.CopyArtifact plugin="{{ variables.JENKINS_PLUGIN_copyartifact }}">
      <project>Bazel</project>
      <filter>**/ci/*</filter>
      <target>input</target>
      <excludes>**/ci/bazel,**/*.bazel.build.tar</excludes>
      <selector class="hudson.plugins.copyartifact.TriggeredBuildSelector">
        <fallbackToLastSuccessful>true</fallbackToLastSuccessful>
        <upstreamFilterStrategy>UseGlobalSetting</upstreamFilterStrategy>
      </selector>
      <flatten>true</flatten>
      <doNotFingerprintArtifacts>false</doNotFingerprintArtifacts>
    </hudson.plugins.copyartifact.CopyArtifact>
    <hudson.tasks.Shell>
      <command>#!/bin/bash

export GITHUB_TOKEN=$(cat $GITHUB_TOKEN_FILE)
export GCS_BUCKET=bazel
export APT_GPG_KEY_ID=$(cat &quot;${APT_GPG_KEY_ID_FILE}&quot;)

# URLs
export GIT_REPOSITORY_URL=&quot;{{ variables.GITHUB_URL }}&quot;

source scripts/ci/build.sh

args=()
for i in input/*; do
  args+=(&quot;$(echo $i | cut -d &quot;=&quot; -f 3)&quot; &quot;$i&quot;)
done

bazel_release &quot;${args[@]}&quot;

mkdir -p output/ci
echo &quot;${RELEASE_EMAIL_RECIPIENT}&quot; &gt; output/ci/recipient
echo &quot;${RELEASE_EMAIL_SUBJECT}&quot; &gt; output/ci/subject
echo &quot;${RELEASE_EMAIL_CONTENT}&quot; &gt; output/ci/content
echo &quot;To: ${RELEASE_EMAIL_RECIPIENT}&quot;
echo &quot;Subject: ${RELEASE_EMAIL_SUBJECT}&quot;
echo &quot;Content: ${RELEASE_EMAIL_CONTENT}&quot;</command>
    </hudson.tasks.Shell>
  </builders>
  <publishers>
    <hudson.plugins.emailext.ExtendedEmailPublisher plugin="{{ variables.JENKINS_PLUGIN_email_ext }}">
      <recipientList>${FILE, path=&quot;output/ci/recipient&quot;}</recipientList>
      <configuredTriggers>
        <hudson.plugins.emailext.plugins.trigger.SuccessTrigger>
          <email>
            <recipientList></recipientList>
            <subject>$PROJECT_DEFAULT_SUBJECT</subject>
            <body>$PROJECT_DEFAULT_CONTENT</body>
            <recipientProviders>
              <hudson.plugins.emailext.plugins.recipients.ListRecipientProvider/>
            </recipientProviders>
            <attachmentsPattern></attachmentsPattern>
            <attachBuildLog>false</attachBuildLog>
            <compressBuildLog>false</compressBuildLog>
            <replyTo>$PROJECT_DEFAULT_REPLYTO</replyTo>
            <contentType>project</contentType>
          </email>
        </hudson.plugins.emailext.plugins.trigger.SuccessTrigger>
      </configuredTriggers>
      <contentType>default</contentType>
      <defaultSubject>${FILE, path=&quot;output/ci/subject&quot;}</defaultSubject>
      <defaultContent>${FILE, path=&quot;output/ci/content&quot;}</defaultContent>
      <attachmentsPattern></attachmentsPattern>
      <presendScript></presendScript>
      <attachBuildLog>false</attachBuildLog>
      <compressBuildLog>false</compressBuildLog>
      <replyTo>bazel-ci@googlegroups.com</replyTo>
      <saveOutput>false</saveOutput>
      <disabled>false</disabled>
    </hudson.plugins.emailext.ExtendedEmailPublisher>
  </publishers>
  <buildWrappers/>
</project>
