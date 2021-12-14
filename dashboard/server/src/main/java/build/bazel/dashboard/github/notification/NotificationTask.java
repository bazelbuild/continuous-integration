package build.bazel.dashboard.github.notification;

import build.bazel.dashboard.config.DashboardConfig;
import build.bazel.dashboard.github.issue.GithubIssue;
import build.bazel.dashboard.github.issue.GithubIssue.Label;
import build.bazel.dashboard.github.issuecomment.GithubIssueCommentService;
import build.bazel.dashboard.github.issuelist.GithubIssueList;
import build.bazel.dashboard.github.issuelist.GithubIssueListService;
import build.bazel.dashboard.github.issuelist.GithubIssueListService.ListParams;
import build.bazel.dashboard.github.issuestatus.GithubIssueStatus;
import build.bazel.dashboard.github.user.GithubUser;
import build.bazel.dashboard.github.user.GithubUserService;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.google.common.base.Strings;
import com.google.common.collect.ImmutableList;
import io.reactivex.rxjava3.core.Completable;
import io.reactivex.rxjava3.core.Flowable;
import io.reactivex.rxjava3.core.Maybe;
import io.reactivex.rxjava3.core.Single;
import java.awt.Color;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;
import javax.mail.MessagingException;
import javax.mail.internet.MimeMessage;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.context.annotation.Profile;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.mail.javamail.MimeMessageHelper;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RestController;

@Profile("notification")
@RestController
@RequiredArgsConstructor
@Slf4j
public class NotificationTask {
  private final DashboardConfig dashboardConfig;
  private final ObjectMapper objectMapper;
  private final JavaMailSender javaMailSender;
  private final GithubIssueListService githubIssueListService;
  private final GithubUserService githubUserService;
  private final GithubIssueCommentService githubIssueCommentService;

  @PostMapping("/internal/github/issues/notifications")
  public void notifyIssueStatus() {
    startNotifyIssueStatus();
  }

  @GetMapping("/internal/github/issues/notifications/triage")
  public Single<String> getTriageTeamNotificationBody() {
    return buildTriageTeamNotificationBody();
  }

  @GetMapping("/internal/github/issues/notifications/{user}")
  public Single<String> getGithubUserNotificationBody(@PathVariable("user") String username) {
    return githubUserService
        .findAll()
        .filter(user -> user.getUsername().equals(username))
        .concatMapSingle(this::buildUserNotificationBody)
        .collect(Collectors.joining());
  }

  @PostMapping("/internal/github/issues/notifications/{user}")
  public Completable notifyGithubUser(@PathVariable("user") String username) {
    return githubUserService
        .findAll()
        .filter(user -> user.getUsername().equals(username))
        .flatMapCompletable(
            user ->
                buildUserNotificationBody(user)
                    .flatMapCompletable(
                        body -> {
                          if (!body.isBlank()) {
                            return Completable.fromCallable(
                                () -> {
                                  sendNotification(user.getEmail(), body, "triage/update");
                                  return null;
                                });
                          }

                          return Completable.complete();
                        }));
  }

  @Scheduled(cron = "0 0 2 * * MON-FRI", zone = "UTC")
  public void startNotifyIssueStatus() {
    notifyTriageTeam().andThen(notifyUsers()).blockingAwait();
  }

  Single<String> buildTriageTeamNotificationBody() {
    ListParams params = new ListParams();
    params.setOwner("bazelbuild");
    params.setRepo("bazel");
    params.setStatus(GithubIssueStatus.Status.TO_BE_REVIEWED);
    return githubIssueListService
        .find(params)
        .flatMap(
            list -> {
              if (list.getTotal() > 0) {
                String reviewLink =
                    dashboardConfig.getHost()
                        + "/issues?q=%7B%22status%22%3A%22TO_BE_REVIEWED%22%2C%22page%22%3A1%7D";
                return buildNotificationBody(reviewLink, "issues", "review", list);
              } else {
                return Single.just("");
              }
            });
  }

  Completable notifyTriageTeam() {
    return buildTriageTeamNotificationBody()
        .flatMapCompletable(
            body -> {
              if (!Strings.isNullOrEmpty(body)) {
                return Completable.fromCallable(
                    () -> {
                      sendNotification(
                          dashboardConfig.getGithub().getNotification().getToNeedReviewEmail(),
                          body,
                          "review");

                      return null;
                    });
              } else {
                return Completable.complete();
              }
            });
  }

  private void sendNotification(String to, String body, String action) throws MessagingException {
    MimeMessage mimeMessage = javaMailSender.createMimeMessage();
    MimeMessageHelper message = new MimeMessageHelper(mimeMessage);
    message.setFrom(dashboardConfig.getGithub().getNotification().getFromEmail());
    message.setTo(to);
    Instant now = Instant.ofEpochSecond(Instant.now().getEpochSecond());
    message.setSubject("Please " + action + " Github issues. " + now.toString());

    StringBuilder text = new StringBuilder();
    text.append("<p>Hi there,</p>");
    text.append(body);
    text.append(
            "<p style=\"font-size:small;color:#666\">----<br>This email is generated by the <a"
                + " href=\"")
        .append(dashboardConfig.getHost())
        .append("\">Dashboard</a>.</p>");

    message.setText(text.toString(), true);
    javaMailSender.send(mimeMessage);
  }

  private Single<String> buildNotificationBody(
      String reviewLink, String type, String action, GithubIssueList list) {
    return Flowable.fromIterable(list.getItems())
        .concatMapMaybe(this::buildIssueListItem)
        .collect(Collectors.toList())
        .map(
            issues -> {
              StringBuilder body = new StringBuilder();

              body.append("<p>You have ");
              appendLink(body, reviewLink, list.getTotal() + " " + type);
              body.append(" to ").append(action).append(". Below are some of them:</p>");

              body.append("<table style=\"text-align: left;\">");

              body.append("<thead>");
              body.append("<tr>");
              body.append("<th>Issue / PR</th>");
              body.append("<th></th>");
              body.append("<th>Author</th>");
              body.append("<th>Participants</th>");
              body.append("</tr>");
              body.append("</thead>");

              body.append("<tbody>");
              for (String issue : issues) {
                body.append(issue);
              }
              body.append("</tbody>");

              body.append("</table>");

              return body.toString();
            });
  }

  private static class Rgb {
    public int r;
    public int g;
    public int b;
  }

  private static Rgb hexToRgb(String hex) {
    Rgb rgb = new Rgb();
    rgb.r = Integer.parseInt(hex.substring(0, 2), 16);
    rgb.g = Integer.parseInt(hex.substring(2, 4), 16);
    rgb.b = Integer.parseInt(hex.substring(4, 6), 16);
    return rgb;
  }

  private void appendLabel(StringBuilder s, Label label) {
    Rgb rgb = hexToRgb(label.getColor());
    float[] hsl = Color.RGBtoHSB(rgb.r, rgb.g, rgb.b, null);
    float perceivedLightness = ((rgb.r * 0.2126f) + (rgb.g * 0.7152f) + (rgb.b * 0.0722f)) / 255;
    float lightnessThreshold = 0.453f;
    float borderThreshold = 0.96f;
    float lightnessSwitch =
        Math.max(0, Math.min((perceivedLightness - lightnessThreshold) * -1000, 1));
    float borderAlpha = Math.max(0, Math.min((perceivedLightness - borderThreshold) * 100, 1));

    s.append("<span style=\"");
    s.append("display: inline-block; padding: 0 7px; margin-right: 4px;");
    s.append("border: 1px solid; border-radius: 2em;");
    s.append("background: rgb(")
        .append(rgb.r)
        .append(", ")
        .append(rgb.g)
        .append(", ")
        .append(rgb.b)
        .append(");");
    s.append("color: hsl(0, 0%, calc(").append(lightnessSwitch).append(" * 100%));");
    s.append("border-color: hsla(")
        .append(hsl[0])
        .append(", calc(")
        .append(hsl[1])
        .append(" * 1%), calc((")
        .append(hsl[2])
        .append(" - 25) * 1%), ")
        .append(borderAlpha)
        .append(");");
    s.append("\">");
    s.append(label.getName());
    s.append("</span>");
  }

  private Maybe<String> buildIssueListItem(GithubIssueList.Item issue) {
    GithubIssue.Data data;
    try {
      data = GithubIssue.parseData(objectMapper, issue.getData());
    } catch (JsonProcessingException e) {
      return Maybe.empty();
    }

    return findParticipants(issue, data)
        .map(
            participants -> {
              StringBuilder body = new StringBuilder();
              body.append("<tr style=\"vertical-align: baseline\">");

              body.append("<td>");
              appendLink(
                  body,
                  String.format(
                      "https://github.com/%s/%s/issues/%s",
                      issue.getOwner(), issue.getRepo(), issue.getIssueNumber()),
                  "#" + issue.getIssueNumber());
              body.append("</td>");

              body.append("<td style=\"white-space: nowrap;\">");
              String title = data.getTitle();
              if (title.length() > 80) {
                title = title.substring(0, 77) + "...";
              }
              boolean isPullRequest = issue.getData().get("pull_request") != null;
              body.append(isPullRequest ? "PR: " : "Issue: ");
              body.append(title);
              body.append("</td>");

              body.append("<td>");
              body.append("@");
              body.append(data.getUser().getLogin());
              body.append("</td>");

              body.append("<td>");
              for (String participant : participants) {
                body.append("@");
                body.append(participant);
                body.append(" ");
              }
              body.append("</td>");

              body.append("<td>");
              for (Label label : data.getLabels()) {
                appendLabel(body, label);
              }
              body.append("</td>");

              body.append("</tr>");

              return body.toString();
            })
        .toMaybe();
  }

  private Single<List<String>> findParticipants(GithubIssueList.Item issue, GithubIssue.Data data) {
    return githubIssueCommentService
        .findIssueComments(issue.getOwner(), issue.getRepo(), issue.getIssueNumber())
        .map(comment -> comment.getUser().getLogin())
        .collect(Collectors.toSet())
        .map(
            participants -> {
              participants.remove(data.getUser().getLogin());
              List<String> result = new ArrayList<>(participants);
              result.sort(String::compareTo);
              return result;
            });
  }

  private void appendLink(StringBuilder sb, String href, String text) {
    sb.append("<a href=\"");
    sb.append(href);
    sb.append("\">");
    sb.append(text);
    sb.append("</a>");
  }

  private Single<String> buildUserNotificationBody(GithubUser user) {
    return Flowable.concatArray(
            buildNeedTriageMessage(user).toFlowable(),
            buildFixP0BugsMessage(user).toFlowable(),
            buildFixP1BugsMessage(user).toFlowable(),
            buildFixP2BugsMessage(user).toFlowable())
        .collect(Collectors.joining());
  }

  private Completable notifyUsers() {
    return githubUserService
        .findAll()
        .flatMapCompletable(
            user ->
                buildUserNotificationBody(user)
                    .flatMapCompletable(
                        body -> {
                          if (!body.isBlank()) {
                            return Completable.fromCallable(
                                () -> {
                                  sendNotification(user.getEmail(), body, "triage/update");
                                  return null;
                                });
                          }

                          return Completable.complete();
                        }));
  }

  Single<String> buildNeedTriageMessage(GithubUser user) {
    ListParams params = new ListParams();
    params.setOwner("bazelbuild");
    params.setRepo("bazel");
    params.setStatus(GithubIssueStatus.Status.REVIEWED);
    params.setActionOwner(user.getUsername());
    return githubIssueListService
        .find(params)
        .flatMap(
            list -> {
              if (list.getTotal() > 0) {
                String reviewLink =
                    dashboardConfig.getHost()
                        + "/issues?q=%7B%22status%22%3A%22REVIEWED%22%2C%22page%22%3A1%2C%22actionOwner%22%3A%22"
                        + user.getUsername()
                        + "%22%7D";
                return buildNotificationBody(reviewLink, "issues", "triage", list);
              }
              return Single.just("");
            });
  }

  Single<String> buildFixP0BugsMessage(GithubUser user) {
    ListParams params = new ListParams();
    params.setOwner("bazelbuild");
    params.setRepo("bazel");
    params.setStatus(GithubIssueStatus.Status.TRIAGED);
    params.setLabels(ImmutableList.of("P0", "type: bug"));
    params.setActionOwner(user.getUsername());

    return githubIssueListService
        .find(params)
        .flatMap(
            list -> {
              if (list.getTotal() > 0) {
                String reviewLink =
                    dashboardConfig.getHost()
                        + "/issues?q=%7B%22status%22%3A%22TRIAGED%22%2C%22page%22%3A1%2C%22labels%22%3A%5B%22P0%22%5D%2C%22actionOwner%22%3A%22"
                        + user.getUsername()
                        + "%22%7D";
                return buildNotificationBody(reviewLink, "P0 bugs", "fix", list);
              }
              return Single.just("");
            });
  }

  Single<String> buildFixP1BugsMessage(GithubUser user) {
    ListParams params = new ListParams();
    params.setOwner("bazelbuild");
    params.setRepo("bazel");
    params.setStatus(GithubIssueStatus.Status.TRIAGED);
    params.setLabels(ImmutableList.of("P1", "type: bug"));
    params.setActionOwner(user.getUsername());

    return githubIssueListService
        .find(params)
        .flatMap(
            list -> {
              if (list.getTotal() > 0) {
                String reviewLink =
                    dashboardConfig.getHost()
                        + "/issues?q=%7B%22status%22%3A%22TRIAGED%22%2C%22page%22%3A1%2C%22labels%22%3A%5B%22P1%22%5D%2C%22actionOwner%22%3A%22"
                        + user.getUsername()
                        + "%22%7D";
                return buildNotificationBody(reviewLink, "P1 bugs", "fix", list);
              }
              return Single.just("");
            });
  }

  Single<String> buildFixP2BugsMessage(GithubUser user) {
    ListParams params = new ListParams();
    params.setOwner("bazelbuild");
    params.setRepo("bazel");
    params.setStatus(GithubIssueStatus.Status.TRIAGED);
    params.setLabels(ImmutableList.of("P2", "type: bug"));
    params.setActionOwner(user.getUsername());

    return githubIssueListService
        .find(params)
        .flatMap(
            list -> {
              if (list.getTotal() > 0) {
                String reviewLink =
                    dashboardConfig.getHost()
                        + "/issues?q=%7B%22status%22%3A%22TRIAGED%22%2C%22page%22%3A1%2C%22labels%22%3A%5B%22P2%22%5D%2C%22actionOwner%22%3A%22"
                        + user.getUsername()
                        + "%22%7D";
                return buildNotificationBody(reviewLink, "P2 bugs", "fix", list);
              }
              return Single.just("");
            });
  }
}
