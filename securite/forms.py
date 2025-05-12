from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Agent

class AgentCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone = forms.CharField(label="Téléphone", max_length=20)  # Ceci est le nom du champ dans le formulaire
   
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
    

class AgentForm(forms.ModelForm):
    # Renommez les champs pour correspondre au modèle
    phone = forms.CharField(label="Téléphone", max_length=20)
    receive_sms = forms.BooleanField(label="Reçoit SMS", required=False)
    receive_email = forms.BooleanField(label="Reçoit Email", required=False)

    class Meta:
        model = Agent
        fields = ['nom', 'email', 'phone', 'receive_sms', 'receive_email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.initial['phone'] = self.instance.telephone
            self.initial['receive_sms'] = self.instance.recoit_sms
            self.initial['receive_email'] = self.instance.recoit_email

    def save(self, commit=True):
        agent = super().save(commit=False)
        # Mappez les noms de champs du formulaire vers le modèle
        agent.telephone = self.cleaned_data['phone']
        agent.recoit_sms = self.cleaned_data['receive_sms']
        agent.recoit_email = self.cleaned_data['receive_email']
        
        if commit:
            agent.save()
        return agent