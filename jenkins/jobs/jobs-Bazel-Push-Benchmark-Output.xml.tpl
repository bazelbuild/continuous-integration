<?xml version='1.0' encoding='UTF-8'?>
<!--
  Copyright 2017 The Bazel Authors. All rights reserved.

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
  <description>Push benchmark output to site</description>
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
      <filter>**/ci/*.json</filter>
      <target>input</target>
      <excludes/>
      <selector class="hudson.plugins.copyartifact.TriggeredBuildSelector">
        <fallbackToLastSuccessful>true</fallbackToLastSuccessful>
        <upstreamFilterStrategy>UseGlobalSetting</upstreamFilterStrategy>
      </selector>
      <flatten>true</flatten>
      <doNotFingerprintArtifacts>false</doNotFingerprintArtifacts>
    </hudson.plugins.copyartifact.CopyArtifact>
    <hudson.tasks.Shell>
      <command>#!/bin/bash
source scripts/ci/build.sh

mkdir benchmark_output
filename=&quot;$(date +%s).json&quot;
cat &lt;&lt; 'EOF' &gt; &quot;benchmark_output/${filename}&quot;
{
  &quot;buildTargetResults&quot;: [{
    &quot;buildTargetConfig&quot;: {&quot;description&quot;: &quot;Target: A Few Files&quot;, &quot;buildTarget&quot;: &quot;AFewFiles&quot;},
    &quot;buildEnvResults&quot;: [{
      &quot;config&quot;: {&quot;description&quot;: &quot;Full clean build&quot;, &quot;cleanBeforeBuild&quot;: true},
      &quot;results&quot;: [{
        &quot;codeVersion&quot;: &quot;v1&quot;,
        &quot;results&quot;: [10.628, 5.821, 5.726]
      }, {
        &quot;codeVersion&quot;: &quot;v2&quot;,
        &quot;results&quot;: [5.834, 5.869, 5.287]
      }, {
        &quot;codeVersion&quot;: &quot;v3&quot;,
        &quot;results&quot;: [6.544, 5.746, 5.731]
      }, {
        &quot;codeVersion&quot;: &quot;v4&quot;,
        &quot;results&quot;: [8.892, 5.63, 6.228]
      }, {
        &quot;codeVersion&quot;: &quot;v5&quot;,
        &quot;results&quot;: [9.28, 5.557, 5.947]
      }]
    }, {
      &quot;config&quot;: {
        &quot;description&quot;: &quot;Incremental build&quot;,
        &quot;incremental&quot;: true
      },
      &quot;results&quot;: [{
        &quot;codeVersion&quot;: &quot;v1&quot;,
        &quot;results&quot;: [0.387, 0.476, 0.366]
      }, {
        &quot;codeVersion&quot;: &quot;v2&quot;,
        &quot;results&quot;: [0.369, 0.413, 0.406]
      }, {
        &quot;codeVersion&quot;: &quot;v3&quot;,
        &quot;results&quot;: [0.381, 0.345, 0.395]
      }, {
        &quot;codeVersion&quot;: &quot;v4&quot;,
        &quot;results&quot;: [0.399, 0.437, 0.393]
      }, {
        &quot;codeVersion&quot;: &quot;v5&quot;,
        &quot;results&quot;: [0.355, 0.385, 0.338]
      }]
    }]
  }, {
    &quot;buildTargetConfig&quot;: {
      &quot;description&quot;: &quot;Target: Many Files&quot;,
      &quot;buildTarget&quot;: &quot;ManyFiles&quot;
    },
    &quot;buildEnvResults&quot;: [{
      &quot;config&quot;: {
        &quot;description&quot;: &quot;Full clean build&quot;,
        &quot;cleanBeforeBuild&quot;: true
      },
      &quot;results&quot;: [{
        &quot;codeVersion&quot;: &quot;v1&quot;,
        &quot;results&quot;: [8.828, 9.149, 8.82]
      }, {
        &quot;codeVersion&quot;: &quot;v2&quot;,
        &quot;results&quot;: [8.856, 9.621, 8.864]
      }, {
        &quot;codeVersion&quot;: &quot;v3&quot;,
        &quot;results&quot;: [9.594, 9.122, 9.11]
      }, {
        &quot;codeVersion&quot;: &quot;v4&quot;,
        &quot;results&quot;: [8.949, 9.38, 8.878]
      }, {
        &quot;codeVersion&quot;: &quot;v5&quot;,
        &quot;results&quot;: [9.1, 9.03, 9.234]
      }]
    }, {
      &quot;config&quot;: {
        &quot;description&quot;: &quot;Incremental build&quot;,
        &quot;incremental&quot;: true
      },
      &quot;results&quot;: [{
        &quot;codeVersion&quot;: &quot;v1&quot;,
        &quot;results&quot;: [3.732, 3.421, 3.521]
      }, {
        &quot;codeVersion&quot;: &quot;v2&quot;,
        &quot;results&quot;: [3.282, 3.695, 3.409]
      }, {
        &quot;codeVersion&quot;: &quot;v3&quot;,
        &quot;results&quot;: [3.434, 3.4, 3.377]
      }, {
        &quot;codeVersion&quot;: &quot;v4&quot;,
        &quot;results&quot;: [3.478, 3.813, 3.402]
      }, {
        &quot;codeVersion&quot;: &quot;v5&quot;,
        &quot;results&quot;: [3.448, 3.865, 3.573]
      }]
    }]
  }, {
    &quot;buildTargetConfig&quot;: {
      &quot;description&quot;: &quot;Target: Long Chained Deps&quot;,
      &quot;buildTarget&quot;: &quot;LongChainedDeps&quot;
    },
    &quot;buildEnvResults&quot;: [{
      &quot;config&quot;: {
        &quot;description&quot;: &quot;Full clean build&quot;,
        &quot;cleanBeforeBuild&quot;: true
      },
      &quot;results&quot;: [{
        &quot;codeVersion&quot;: &quot;v1&quot;,
        &quot;results&quot;: [16.47, 16.052, 15.845]
      }, {
        &quot;codeVersion&quot;: &quot;v2&quot;,
        &quot;results&quot;: [16.918, 16.22, 15.814]
      }, {
        &quot;codeVersion&quot;: &quot;v3&quot;,
        &quot;results&quot;: [15.634, 16.081, 15.706]
      }, {
        &quot;codeVersion&quot;: &quot;v4&quot;,
        &quot;results&quot;: [16.197, 15.789, 16.26]
      }, {
        &quot;codeVersion&quot;: &quot;v5&quot;,
        &quot;results&quot;: [16.166, 16.645, 16.138]
      }]
    }, {
      &quot;config&quot;: {
        &quot;description&quot;: &quot;Incremental build&quot;,
        &quot;incremental&quot;: true
      },
      &quot;results&quot;: [{
        &quot;codeVersion&quot;: &quot;v1&quot;,
        &quot;results&quot;: [10.582, 10.368, 10.538]
      }, {
        &quot;codeVersion&quot;: &quot;v2&quot;,
        &quot;results&quot;: [10.474, 10.514, 11.613]
      }, {
        &quot;codeVersion&quot;: &quot;v3&quot;,
        &quot;results&quot;: [10.912, 10.873, 10.512]
      }, {
        &quot;codeVersion&quot;: &quot;v4&quot;,
        &quot;results&quot;: [10.482, 10.799, 11.059]
      }, {
        &quot;codeVersion&quot;: &quot;v5&quot;,
        &quot;results&quot;: [11.441, 10.622, 10.501]
      }]
    }]
  }, {
    &quot;buildTargetConfig&quot;: {
      &quot;description&quot;: &quot;Target: Parallel Deps&quot;,
      &quot;buildTarget&quot;: &quot;ParallelDeps&quot;
    },
    &quot;buildEnvResults&quot;: [{
      &quot;config&quot;: {
        &quot;description&quot;: &quot;Full clean build&quot;,
        &quot;cleanBeforeBuild&quot;: true
      },
      &quot;results&quot;: [{
        &quot;codeVersion&quot;: &quot;v1&quot;,
        &quot;results&quot;: [8.541, 8.353, 8.603]
      }, {
        &quot;codeVersion&quot;: &quot;v2&quot;,
        &quot;results&quot;: [8.42, 8.89, 8.578]
      }, {
        &quot;codeVersion&quot;: &quot;v3&quot;,
        &quot;results&quot;: [8.955, 7.972, 8.242]
      }, {
        &quot;codeVersion&quot;: &quot;v4&quot;,
        &quot;results&quot;: [8.579, 8.646, 8.744]
      }, {
        &quot;codeVersion&quot;: &quot;v5&quot;,
        &quot;results&quot;: [8.456, 8.494, 9.096]
      }]
    }, {
      &quot;config&quot;: {
        &quot;description&quot;: &quot;Incremental build&quot;,
        &quot;incremental&quot;: true
      },
      &quot;results&quot;: [{
        &quot;codeVersion&quot;: &quot;v1&quot;,
        &quot;results&quot;: [0.807, 0.759, 0.807]
      }, {
        &quot;codeVersion&quot;: &quot;v2&quot;,
        &quot;results&quot;: [0.761, 0.764, 1.029]
      }, {
        &quot;codeVersion&quot;: &quot;v3&quot;,
        &quot;results&quot;: [0.782, 0.902, 0.817]
      }, {
        &quot;codeVersion&quot;: &quot;v4&quot;,
        &quot;results&quot;: [0.818, 0.745, 0.794]
      }, {
        &quot;codeVersion&quot;: &quot;v5&quot;,
        &quot;results&quot;: [0.798, 0.781, 0.815]
      }]
    }]
  }]
}
EOF
push_benchmark_output_to_site &quot;${filename}&quot; &quot;perf.bazel.build&quot;
      </command>
    </hudson.tasks.Shell>
  </builders>
  <publishers/>
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