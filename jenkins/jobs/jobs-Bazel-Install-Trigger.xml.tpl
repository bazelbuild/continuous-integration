<?xml version='1.0' encoding='UTF-8'?>
<!--
  Copyright 2016 The Bazel Authors. All rights reserved.

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
  <description>Just trigger Bazel-Install to run it on all slaves</description>
  <keepDependencies>false</keepDependencies>
  <properties/>
  <assignedNode>deploy</assignedNode>
  <canRoam>false</canRoam>
  <disabled>false</disabled>
  <blockBuildWhenDownstreamBuilding>false</blockBuildWhenDownstreamBuilding>
  <blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>
  <triggers/>
  <concurrentBuild>false</concurrentBuild>
  <builders>
    <hudson.plugins.parameterizedtrigger.TriggerBuilder plugin="{{ variables.JENKINS_parameterized_trigger }}">
      <configs>
        <hudson.plugins.parameterizedtrigger.BlockableBuildTriggerConfig>
          <configs>
            <hudson.plugins.parameterizedtrigger.CurrentBuildParameters/>
          </configs>
          <configFactories>
            <org.jvnet.jenkins.plugins.nodelabelparameter.parameterizedtrigger.AllNodesForLabelBuildParameterFactory plugin="{{ variables.JENKINS_nodelabelparameter }}">
              <name>PLATFORM_NAME</name>
              <nodeLabel>install-bazel</nodeLabel>
              <ignoreOfflineNodes>true</ignoreOfflineNodes>
            </org.jvnet.jenkins.plugins.nodelabelparameter.parameterizedtrigger.AllNodesForLabelBuildParameterFactory>
          </configFactories>
          <projects>Bazel-Install</projects>
          <condition>ALWAYS</condition>
          <triggerWithNoParameters>false</triggerWithNoParameters>
          <block>
            <buildStepFailureThreshold>
              <name>FAILURE</name>
              <ordinal>2</ordinal>
              <color>RED</color>
              <completeBuild>true</completeBuild>
            </buildStepFailureThreshold>
            <unstableThreshold>
              <name>UNSTABLE</name>
              <ordinal>1</ordinal>
              <color>YELLOW</color>
              <completeBuild>true</completeBuild>
            </unstableThreshold>
            <failureThreshold>
              <name>FAILURE</name>
              <ordinal>2</ordinal>
              <color>RED</color>
              <completeBuild>true</completeBuild>
            </failureThreshold>
          </block>
          <buildAllNodesWithLabel>false</buildAllNodesWithLabel>
        </hudson.plugins.parameterizedtrigger.BlockableBuildTriggerConfig>
      </configs>
    </hudson.plugins.parameterizedtrigger.TriggerBuilder>
  </builders>
  <publishers>
    {% if variables.SEND_EMAIL == "1" %}
    <hudson.tasks.Mailer>
      <recipients>{{ variables.BAZEL_BUILD_RECIPIENT }}</recipients>
      <dontNotifyEveryUnstableBuild>false</dontNotifyEveryUnstableBuild>
      <sendToIndividuals>false</sendToIndividuals>
    </hudson.tasks.Mailer>
    {% endif %}
    <hudson.plugins.parameterizedtrigger.BuildTrigger>
      <configs>
        <hudson.plugins.parameterizedtrigger.BuildTriggerConfig>
          <configs>
            <hudson.plugins.parameterizedtrigger.CurrentBuildParameters/>
          </configs>
          <projects>Tutorial, {{ variables.GITHUB_JOBS }}</projects>
          <condition>UNSTABLE_OR_BETTER</condition>
          <triggerWithNoParameters>false</triggerWithNoParameters>
        </hudson.plugins.parameterizedtrigger.BuildTriggerConfig>
      </configs>
    </hudson.plugins.parameterizedtrigger.BuildTrigger>
  </publishers>
  <buildWrappers>
    <hudson.plugins.build__timeout.BuildTimeoutWrapper>
      <strategy class="hudson.plugins.build_timeout.impl.AbsoluteTimeOutStrategy">
        <timeoutMinutes>240</timeoutMinutes>
      </strategy>
      <operationList>
        <hudson.plugins.build__timeout.operations.FailOperation/>
        <hudson.plugins.build__timeout.operations.WriteDescriptionOperation>
          <description>Timed out</description>
        </hudson.plugins.build__timeout.operations.WriteDescriptionOperation>
      </operationList>
    </hudson.plugins.build__timeout.BuildTimeoutWrapper>
  </buildWrappers>
</project>
