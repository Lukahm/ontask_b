# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function

from celery.task.control import inspect
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.shortcuts import redirect, render
from django.utils.translation import ugettext_lazy as _
from django.urls import reverse

import logs.ops
from action.models import Action
from action.views_action import preview_response
from ontask.permissions import is_instructor
from ontask.tasks import send_email_messages
from workflow.ops import get_workflow
from .forms import EmailActionForm


@user_passes_test(is_instructor)
def request_data(request, pk):
    """
    Request data to send emails. Form asking for subject line, email column,
    etc.
    :param request: HTTP request (GET)
    :param pk: Action key
    :return:
    """

    # Get the action attached to this request
    try:
        action = Action.objects.filter(
            Q(workflow__user=request.user) |
            Q(workflow__shared=request.user)).distinct().get(pk=pk)
    except ObjectDoesNotExist:
        return redirect('workflow:index')

    workflow = get_workflow(request, action.workflow.id)
    if not workflow:
        return redirect('workflow:index')

    # Create the form to ask for the email subject and other information
    form = EmailActionForm(request.POST or None,
                           column_names=workflow.get_column_names())

    # Verify that celery is running!
    celery_stats = None
    try:
        celery_stats = inspect().stats()
    except Exception as e:
        pass
    # If the stats are empty, celery is not running.
    if not celery_stats:
        messages.error(
            request,
            _('Unable to send emails due to a misconfiguration. '
            'Ask your system administrator to enable email queueing.'))
        return redirect(reverse('action:index'))

    # Process the GET or invalid
    if request.method == 'GET' or not form.is_valid():
        # Get the number of rows from the action
        filter_c = action.conditions.filter(is_filter=True).first()
        num_msgs = filter_c.n_rows_selected if filter_c else -1
        if num_msgs == -1:
            # There is no filter in the action, so take the number of rows
            num_msgs = workflow.nrows

        # Render the form
        return render(request,
                      'action/request_email_data.html',
                      {'action': action,
                       'num_msgs': num_msgs,
                       'form': form})

    # Requet is a POST and is valid
    subject = form.cleaned_data['subject']
    email_column = form.cleaned_data['email_column']
    cc_email = [x.strip() for x in form.cleaned_data['cc_email'].split(',')
                if x]
    bcc_email = [x.strip() for x in form.cleaned_data['bcc_email'].split(',')
                 if x]
    send_confirmation = form.cleaned_data['send_confirmation']
    track_read = form.cleaned_data['track_read']

    # Log the event
    log_id = logs.ops.put(request.user,
                          'schedule_email_execute',
                          action.workflow,
                          {'action': action.name,
                           'action_id': action.id,
                           'subject': subject,
                           'email_column': email_column,
                           'cc_email': cc_email,
                           'bcc_email': bcc_email,
                           'send_confirmation': send_confirmation,
                           'track_read': track_read,
                           'status': 'pre-execution'})

    # Send the emails!
    send_email_messages.delay(request.user.id,
                              action.id,
                              form.cleaned_data['subject'],
                              form.cleaned_data['email_column'],
                              request.user.email,
                              cc_email,
                              bcc_email,
                              send_confirmation,
                              track_read,
                              log_id)

    # If the export has been requested, go there and send it as
    # response
    context = {'log_id': log_id}
    if form.cleaned_data['export_wf']:
        context['download'] = True

    # Successful processing.
    return render(request,
                  'action/email_done.html',
                  context)


@user_passes_test(is_instructor)
def preview(request, pk, idx):
    """
    HTML request and the primary key of an action to preview one of its
    instances. The request must provide and additional parameter idx to
    denote which instance to show.

    :param request: HTML request object
    :param pk: Primary key of the an action for which to do the preview
    :param idx: Index of the element to preview
    :return:
    """

    subject_content = request.GET.get('subject_content',
                                      _('THE SUBJECT WILL BE INSERTED HERE'))
    return preview_response(
        request,
        pk,
        idx,
        'action/includes/partial_email_preview.html',
        subject_content)

    # This function is redundant, but I thought I could include here the
    # subject, but it is too soon in the workflow and it is still unsubmitted.
