from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import gettext_lazy as _


class PlatformLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        c = "mt-1 w-full rounded-xl border border-slate-300 px-3 py-2 text-base"
        self.fields["username"].label = _("Telegram ID")
        self.fields["username"].widget.attrs.update({"class": c, "autocomplete": "username"})
        self.fields["password"].widget.attrs.update({"class": c, "autocomplete": "current-password"})


class BroadcastForm(forms.Form):
    message = forms.CharField(
        label=_("Message"),
        widget=forms.Textarea(attrs={"rows": 4, "class": "w-full rounded-xl border border-slate-300 px-3 py-2"}),
        max_length=4000,
    )
    segment = forms.ChoiceField(
        label=_("Recipients"),
        choices=[
            ("all", _("All users")),
            ("sellers", _("Sellers only")),
            ("buyers", _("Buyers only")),
        ],
        initial="sellers",
        widget=forms.Select(
            attrs={"class": "mt-1 w-full rounded-xl border border-slate-300 px-3 py-2 text-base"}
        ),
    )
