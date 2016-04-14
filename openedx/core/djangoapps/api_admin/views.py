"""Views for API management."""
import logging

from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.core.urlresolvers import reverse_lazy, reverse
from django.shortcuts import redirect
from django.utils.translation import ugettext as _
from django.views.generic import View
from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView
from oauth2_provider.generators import generate_client_secret, generate_client_id
from oauth2_provider.models import get_application_model
from oauth2_provider.views import ApplicationRegistration

from edxmako.shortcuts import render_to_response
from openedx.core.djangoapps.api_admin.decorators import require_api_access
from openedx.core.djangoapps.api_admin.forms import ApiAccessRequestForm
from openedx.core.djangoapps.api_admin.models import ApiAccessRequest

log = logging.getLogger(__name__)

Application = get_application_model()  # pylint: disable=invalid-name


class ApiRequestView(CreateView):
    """Form view for requesting API access."""
    form_class = ApiAccessRequestForm
    template_name = 'api_admin/api_access_request_form.html'
    success_url = reverse_lazy('api_admin:api-status')

    def get(self, request):
        """
        If the requesting user has already requested API access, redirect
        them to the client creation page.
        """
        if ApiAccessRequest.api_access_status(request.user) is not None:
            return redirect(reverse('api_admin:api-status'))
        return super(ApiRequestView, self).get(request)

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.site = get_current_site(self.request)
        return super(ApiRequestView, self).form_valid(form)


class ApiRequestStatusView(ApplicationRegistration):
    """View for confirming our receipt of an API request."""

    success_url = reverse_lazy('api_admin:api-status')

    def get(self, request, form=None):  # pylint: disable=arguments-differ
        """
        If the user has not created an API request, redirect them to the
        request form. Otherwise, display the status of their API
        request. We take `form` as an optional argument so that we can
        display validation errors correctly on the page.
        """
        if form is None:
            form = self.get_form_class()()

        user = request.user
        try:
            api_request = ApiAccessRequest.objects.get(user=user)
        except ApiAccessRequest.DoesNotExist:
            return redirect(reverse('api_admin:api-request'))
        try:
            application = Application.objects.get(user=user)
        except Application.DoesNotExist:
            application = None

        # We want to fill in a few fields ourselves, so remove them
        # from the form so that the user doesn't see them.
        for field in ('client_type', 'client_secret', 'client_id', 'authorization_grant_type'):
            form.fields.pop(field)

        return render_to_response('api_admin/status.html', {
            'status': api_request.status,
            'api_support_link': _('TODO'),
            'api_support_email': settings.API_ACCESS_MANAGER_EMAIL,
            'form': form,
            'application': application,
        })

    def get_form(self, form_class=None):
        form = super(ApiRequestStatusView, self).get_form(form_class)
        # Copy the data, since it's an immutable QueryDict.
        copied_data = form.data.copy()
        # Now set the fields that were removed earlier. We give them
        # confidential client credentials, and generate their client
        # ID and secret.
        copied_data.update({
            'authorization_grant_type': Application.GRANT_CLIENT_CREDENTIALS,
            'client_type': Application.CLIENT_CONFIDENTIAL,
            'client_secret': generate_client_secret(),
            'client_id': generate_client_id(),
        })
        form.data = copied_data
        return form

    def form_valid(self, form):
        # Delete any existing applications if the user has decided to regenerate their credentials
        Application.objects.filter(user=self.request.user).delete()
        return super(ApiRequestStatusView, self).form_valid(form)

    def form_invalid(self, form):
        return self.get(self.request, form)

    @require_api_access
    def post(self, request):
        return super(ApiRequestStatusView, self).post(request)


class ApiTosView(TemplateView):
    """View to show the API Terms of Service."""

    template_name = 'api_admin/terms_of_service.html'
