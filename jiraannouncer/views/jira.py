import random
import time

import simplejson
from pyramid.view import view_config

from ..utils import send, getlast, devsay
import logging

log = logging.getLogger(__name__)
OFFSET = 5


@view_config(route_name='jira', renderer="json")
def jira(request):
    """Handle JIRA events."""
    lastmessage = getlast()
    try:
        data = request.json_body
    except:
        log.error("Failed to decode JSON from body. Dump:")
        log.debug(request.body)
        devsay("A JIRA payload couldn't be decoded. Absolver, check the logfile!",
               request)
        return
    request_type = data['webhookEvent']

    if 'issue' in data:
        issue_key = data['issue']['key']
    elif 'user' in data:
        issue_key = data['user']['key']
    elif 'project' in data:
        issue_key = data['project']['key']
    else:
        issue_key = "JIRA"

    if "TRAIN-" in issue_key or "OV-" in issue_key or "DRR-" in issue_key or "DOS-" in issue_key or "CID-" in issue_key:
        channels = ["#doersofstuff"]
    elif "OPS-" in issue_key:
        channels = ["#rat-ops"]
    elif "SPARK-" in issue_key or "MECHA-" in issue_key:
        channels = ["#mechadev"]
    elif "SQUAD-" in issue_key:
        channels = ["#squad"]
    elif "TMGMT-" in issue_key or "ADM-" in issue_key or "OVPR-" in issue_key:
        channels = ["#operations"]
    elif "QMS-" in issue_key:
        channels = ['#absdev', '#rattech']
    elif "WEB-" in issue_key:
        channels = ['#bbsdev', '#rattech']
    else:
        channels = ["#rattech"]

    domessage = True
    if 'issue' in data:
        fields = data['issue']['fields']
    else:
        log.debug("No issue key in JIRA webhook body, dumping:")
        log.debug(request.body)
        fields = data
    if request_type == 'jira:issue_created':
        if "OV-" in issue_key or "DRR-" in issue_key:
            message = (f"\x0307{fields['issuetype']['name']}"
                       f"\x03 Created: \x02{fields['summary']}"
                       f"\x02 in {fields['project']['name']}"
                       f" by \x02\x0314{fields['reporter']['displayName']}"
                       f"\x02\x03. (\x02\x0311https://jira.fuelrats.com/browse/{issue_key}\x03\x02)")
        else:
            if 'priority' in fields:
                message = (
                    f"Issue Created: \x02\x0307{fields['issuetype']['name']}\x02\x03 [\x02\x0306"
                    f"{issue_key}\x03\x02] Priority: {fields['priority']['name']} in \x02"
                    f"{fields['project']['name']}\x02(\x02{fields['project']['key']}\x02) by \x02\x0314"
                    f"{fields['reporter']['displayName']}.\x03\x02 \"{fields['summary']}"
                    f"\". (\x02\x0311https://jira.fuelrats.com/browse/{issue_key}\x03\x02)")
            else:
                message = (
                    f"Issue Created: \x02\x0307{fields['issuetype']['name']}\x02\x03 [\x02\x0306"
                    f"{issue_key}\x03\x02] in \x02{fields['project']['name']}\x02(\x02"
                    f"{fields['project']['key']}\x02) by \x02\x0314{fields['reporter']['displayName']}"
                    f".\x03\x02 \"{fields['summary']}\". (\x02\x0311https://jira.fuelrats.com/browse/"
                    f"{issue_key}\x03\x02)")
    elif request_type == 'jira:issue_updated':
        if "OV-" in issue_key or "DRR-" in issue_key:
            if data['user']['displayName'] == "Fuel Rats Automation":
                message = "Fuel Rats Automation cleanup done."
                domessage = False
                this_kennel = str(random.random())
                kfile = open("kennel.p", "w")
                kfile.write(this_kennel)
                kfile.close()
                time.sleep(2)
                kfile2 = open("kennel.p", "r")
                if kfile2.readline() == this_kennel:
                    domessage = True
                else:
                    log.info("JIRA Automation report suppressed")
            else:
                if (data['issue']['fields']['status']['id'] == "10400" or
                        data['issue']['fields']['status']['id'] == "10600"):
                    status_colour = "\x0304"
                else:
                    status_colour = "\x0303"
                message = (
                    f"\x0307{fields['issuetype']['name']}\x03 {status_colour}{fields['status']['name']}"
                    f"\x03: \x02{fields['summary']}\x02 in {fields['project']['name']} by \x02\x0314"
                    f"{data['user']['displayName']}\x02\x03. (\x02\x0311https://jira.fuelrats.com/browse/"
                    f"{issue_key}\x03\x02)")
        else:
            if 'changelog' in data:
                if len(data['changelog']['items']) == 1:
                    if data['changelog']['items'][0]['field'] == "Rank" or \
                            data['changelog']['items'][0]['field'] == "Sprint":
                        log.info("Rank or sprint change ignored")
                        domessage = False
                        return
            if "user" not in data:
                user = "Nep"
            else:
                user = data['user']['displayName']

            if data['issue_event_type_name'] == "issue_commented":
                update_type = "Commented:"
            elif data['issue_event_type_name'] == "issue_assigned":
                update_type = "Assigned to " + data['issue']['fields'][
                    'assignee']['displayName'] + ":"
            else:
                update_type = "Updated:"

            if "SQUAD-" in issue_key:
                if fields['status']['id'] == "10100":
                    status_colour = "\x0304"
                else:
                    status_colour = "\x0303"
            else:
                status_colour = "\x0303"

            message = (
                f"Issue {update_type} \x02\x0307{fields['issuetype']['name']}\x02\x03 \""
                f"{fields['summary']}\" [\x02\x0306{data['issue']['key']}\x03\x02] in \x02"
                f"{fields['project']['name']}\x02(\x02{fields['project']['key']}\x02) by \x0314\x02"
                f"{user}.\x03\x02 Status: \x02{status_colour}{fields['status']['name']}\x03\x02. "
                f"(\x0311\x02https://jira.fuelrats.com/browse/{issue_key}\x03\x02)")
    elif request_type == 'jira:issue_deleted':
        message = (
            f"Issue Deleted: \x02\x0307{fields['issuetype']['name']}\x02\x03 \"{fields['summary']}"
            f"\" [\x02\x0306{data['issue']['key']}\x03\x02] in \x02{fields['project']['name']}\x02(\x02"
            f"{fields['project']['key']}\x02) by \x0314\x02{data['user']['displayName']}.\x03\x02")
    elif request_type == 'user_created':
        message = (f"User created: \x02\x0307{data['user']['key']}\x02\x03 (\x02\x0311"
                   f"{data['user']['emailAddress']}\x02\x03)")
        domessage = False
    elif request_type == 'user_deleted':
        message = (f"User deleted: \x02\x0307{data['user']['key']}\x02\x03 (\x02\x0311"
                   f"{data['user']['name']}\x02\x03)")
    elif request_type == 'jira:version_created':
        message = f"Version created: \x02\x0307{data['version']['name']}\x02\x03 of {data['project'] or '<unset>'}"
    elif request_type == 'project_created':
        message = (f"Project created: \x02\x0307{data['project']['name']}\x02\x03 [\x02\x0306"
                   f"{data['project']['key']}\x03\x02] under \x02\x0314{data['project']['projectLead']['key']}"
                   f"({data['project']['projectLead']['displayName']})")
    elif request_type == 'project_deleted':
        message = (f"Project deleted: \x02\x0307{data['project']['name']}\x02\x03 [\x02x0308"
                   f"{data['project']['key']}\x03\x02] under \x02\x0314{data['project']['projectLead']['key']}"
                   f" ({data['project']['projectLead']['displayName']})")
    elif request_type in ['comment_created', 'comment_updated']:
        message = None  # Not sure we actually want spam every time a comment is made.
        domessage = False
    else:
        message = "JIRA unhandled event: " + request_type
        devsay(f"An unhandled JIRA event '{request_type}' was passed to webhook. Absolver should implement.",
               request)
        log.debug(f"Unhandled JIRA event: {message}")
        return

    msgshort = {"time": time.time(), "type": request_type, "key": issue_key, "full": message}

    squadstatuschange = False
    if "SQUAD-" in issue_key:
        if 'changelog' in data:
            for item in data['changelog']['items']:
                if item['field'] == "status":
                    squadstatuschange = True

    if (lastmessage['type'] == request_type and lastmessage['key'] == issue_key and
            lastmessage['time'] > time.time() - (OFFSET * 60) and
            data['issue_event_type_name'] != "issue_commented" and
            squadstatuschange is False):
        log.warn(f"Duplicate squad message, skipping: {message}")
        return
    elif domessage:
        for channel in channels:
            send(channel, f"[\x0315JIRA\x03] {message}", msgshort, request)
        return
