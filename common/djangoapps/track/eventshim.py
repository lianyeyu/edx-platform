"""
EventShims that create
"""

# pylint: disable=missing-docstring

import json
import logging

from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import UsageKey

log = logging.getLogger(__name__)


class DottedPathMapping(object):
    """
    Dictionary-like object for creating keys of dotted paths.

    If a key is created that ends with a dot, it will be treated as a path
    prefix.  Any value whose prefix matches the dotted path can be used
    as a key for that value, but only the most specific match will
    be used.
    """

    def __init__(self, registry=None):
        self._match_registry = {}
        self._prefix_registry = {}
        self.update(registry or {})

    def __contains__(self, key):
        try:
            _ = self[key]
            return True
        except KeyError:
            return False

    def __getitem__(self, key):
        if key in self._match_registry:
            return self._match_registry[key]
        if isinstance(key, basestring):
            for prefix in sorted(self._prefix_registry, reverse=True):
                if key.startswith(prefix):
                    return self._prefix_registry[prefix]
        raise KeyError('Key {} not found in {}'.format(key, type(self)))

    def __setitem__(self, key, value):
        if key.endswith('.'):
            self._prefix_registry[key] = value
        else:
            self._match_registry[key] = value

    def __delitem__(self, key):
        if key.endswith('.'):
            del self._prefix_registry[key]
        else:
            del self._match_registry[key]

    def get(self, key, default=None):
        try:
            self[key]
        except KeyError:
            return default

    def update(self, dict_):
        for key, value in dict_:
            self[key] = value

    def keys(self):
        return self._match_registry.keys() + self._prefix_registry.keys()


class EventShimRegistry(object):
    """
    Registry to track which EventShims handle which events.  The EventShim
    must define a `shim_name` attribute which contains the name or prefix of the
    event names it tracks.  Any shim_name  that ends with a `.` will match all events
    that share its prefix.  A shim name without a trailing dot only processes exact
    matches.
    """

    mapping = DottedPathMapping()

    @classmethod
    def register(cls, shim):
        """
        Decorator to register an EventShim.  It must have a `shim_name` class attribute
        defined.
        """
        cls.mapping[shim.shim_name] = shim
        return shim

    @classmethod
    def create_shim(cls, event):
        """
        Create a shimmed version of the given event.

        If no shim is registered to handle the event, this raises a KeyError.
        """
        name = event.get(u'name')
        return cls.mapping[name](event)  # pylint: disable=no-member


class EventShim(dict):
    """
    Creates a shim to modify analytics events based on event type.

    To use the event shim, instantiate it using the `EventShim.create_shim()`
    classmethod with the event dictionary as the sole argument, and then call
    `event_shim.shim()` to modify the shim to the format required for output.

    Custom shims will want to define some or all of the following values

    Attributes:

        shim_name:
            This is the name of the event you want to shim.  If the name
            ends with a `'.'`, it will be treated as a *prefix shim*.  All
            other names denote *exact shims*.

            A *prefix shim* will handle any event whose name begins with the
            name of the prefix shim.  Only the most specific match will be
            used, so if a shim exists with a name of `'edx.ui.lms.'` and
            another shim has the name `'edx.ui.lms.sequence.'` then an event
            called `'edx.ui.lms.sequence.tab_selected'` will be handled by the
            `'edx.ui.lms.sequence.'` shim.

            An *exact shim* will only handle events whose name matches name of
            the shim exactly.

            Exact shims always take precedence over prefix shims.

            Shims without a name will not be added to the registry, and cannot
            be accessed via the `EventShim.create_shim()` classmethod.

        is_legacy_event:
            If an event is a legacy event, it needs to set event_type to
            the legacy name for the event, and may need to set certain
            event fields to maintain backward compatiblity.  If an event
            needs to provide legacy support in some contexts, `is_legacy_event`
            can be defined as a property to add dynamic behavior.

            Default: False

        legacy_event_type:
            If the event is or can be a legacy event, it should define
            the legacy value for the event_type field here.

    Processing methods.  Override these to provide the behavior needed for your
    particular EventShim:

        self.process_legacy_fields():

            This method should modify the event payload in any way necessary to
            support legacy event types.  It will only be run if
            `is_legacy_event` returns a True value.

        self.process_event()
            TODO:
    """

    # factory method

    # Abstract Properties

    is_legacy_event = False

    @property
    def legacy_event_type(self):
        raise NotImplementedError

    # Convenience properties

    @property
    def name(self):
        return self[u'name']

    @property
    def context(self):
        return self[u'context']

    @property
    def event(self):
        return self[u'event']

    # Shimming methods

    def shim(self):
        if self.is_legacy_event:
            self.set_legacy_event_type()
            self.process_legacy_fields()
        self.process_event()

    def set_legacy_event_type(self):
        self['event_type'] = self.legacy_event_type

    def process_legacy_fields(self):
        pass

    def process_event(self):
        pass


@EventShimRegistry.register
class TabSelectedEventShim(EventShim):
    """
    Shim to maintain backward compatiblity with seq_goto events.
    """

    shim_name = u'edx.ui.lms.sequence.tab_selected'
    is_legacy_event = True
    legacy_event_type = u'seq_goto'

    def process_legacy_fields(self):
        self.event[u'old'] = self.event[u'current_tab']
        self.event[u'new'] = self.event[u'target_tab']


class _BaseLinearSequenceEventShim(EventShim):
    """
    Common functionality for shimming
    `edx.ui.lms.sequence.{next,previous}_selected` events.
    """

    offset = None

    @property
    def is_legacy_event(self):
        return not self.crosses_boundary()

    def process_legacy_fields(self):
        self.event[u'old'] = self.event[u'current_tab']
        self.event[u'new'] = self.event[u'current_tab'] + self.offset

    def crosses_boundary(self):
        raise NotImplementedError


@EventShimRegistry.register
class NextSelectedEventShim(_BaseLinearSequenceEventShim):
    """
    Shim to maintain backward compatiblity with seq_next events.
    """

    shim_name = u'edx.ui.lms.sequence.next_selected'
    offset = 1
    legacy_event_type = u'seq_next'

    def crosses_boundary(self):
        return self.event[u'current_tab'] == self.event[u'tab_count']


@EventShimRegistry.register
class PreviousSelectedEventShim(_BaseLinearSequenceEventShim):
    """
    Shim to maintain backward compatiblity with seq_prev events.
    """

    shim_name = u'edx.ui.lms.sequence.previous_selected'
    offset = -1
    legacy_event_type = u'seq_prev'

    def crosses_boundary(self):
        return self.event[u'current_tab'] == 1


@EventShimRegistry.register
class VideoEventShim(EventShim):
    """
    Converts new format video events into the legacy video event format.

    Mobile devices cannot actually emit events that exactly match their
    counterparts emitted by the LMS javascript video player. Instead of
    attempting to get them to do that, we instead insert a shim here that
    converts the events they *can* easily emit and converts them into the
    legacy format.

    TODO: Remove this shim and perform the conversion as part of some batch
    canonicalization process.
    """
    shim_name = u'edx.video.'

    name_to_event_type_map = {
        u'edx.video.played': u'play_video',
        u'edx.video.paused': u'pause_video',
        u'edx.video.stopped': u'stop_video',
        u'edx.video.loaded': u'load_video',
        u'edx.video.position.changed': u'seek_video',
        u'edx.video.seeked': u'seek_video',
        u'edx.video.transcript.shown': u'show_transcript',
        u'edx.video.transcript.hidden': u'hide_transcript',
    }

    is_legacy_event = True

    @property
    def legacy_event_type(self):
        return self.name_to_event_type_map[self.name]

    def process_event(self):
        if self.name not in self.name_to_event_type_map:
            return
        # import pdb; pdb.set_trace()

        # Convert edx.video.seeked to edx.video.position.changed because edx.video.seeked was not intended to actually
        # ever be emitted.
        if self.name == "edx.video.seeked":
            self['name'] = "edx.video.position.changed"

        if 'event' not in self:
            return
        payload = self.event

        if 'module_id' in payload:
            module_id = payload['module_id']
            try:
                usage_key = UsageKey.from_string(module_id)
            except InvalidKeyError:
                log.warning('Unable to parse module_id "%s"', module_id, exc_info=True)
            else:
                payload['id'] = usage_key.html_id()

            del payload['module_id']

        if 'current_time' in payload:
            payload['currentTime'] = payload.pop('current_time')

        if 'context' in self:
            context = self.context

            # Converts seek_type to seek and skip|slide to onSlideSeek|onSkipSeek
            if 'seek_type' in payload:
                seek_type = payload['seek_type']
                if seek_type == 'slide':
                    payload['type'] = "onSlideSeek"
                elif seek_type == 'skip':
                    payload['type'] = "onSkipSeek"
                del payload['seek_type']

            # Handle seek bug in iOS
            if self._build_requests_plus_30_for_minus_30(context):
                if self._user_requested_plus_30_skip(payload):
                    payload['requested_skip_interval'] = -30

            # For the Android build that isn't distinguishing between skip/seek
            if 'requested_skip_interval' in payload:
                if abs(payload['requested_skip_interval']) != 30:
                    if 'type' in payload:
                        payload['type'] = 'onSlideSeek'

            if 'open_in_browser_url' in context:
                self['page'] = context.pop('open_in_browser_url').rpartition('/')[0]

        self['event'] = json.dumps(payload)

    @staticmethod
    def _build_requests_plus_30_for_minus_30(context):
        """
        iOS build 1.0.02 has a bug where it returns a +30 second skip when
        it should be returning -30.

        Returns True if this build
        """

        app_version = context['application']['version']
        app_name = context['application']['name']
        return app_version == "1.0.02" and app_name == "edx.mobileapp.iOS"

    @staticmethod
    def _user_requested_plus_30_skip(payload):
        """
        If the user requested a +30 second skip, return True.
        """

        if 'requested_skip_interval' in payload and 'type' in payload:
            interval = payload['requested_skip_interval']
            action = payload['type']
            return interval == 30 and action == "onSkipSeek"
        else:
            return False
