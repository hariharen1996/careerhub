from django.shortcuts import redirect

class RedirectUserMixin:
    def dispatch(self,*args,**kwargs):
        if self.request.user.is_authenticated:
            return redirect('job-home')
        return super().dispatch(*args,**kwargs)
