from rest_framework.routers import DefaultRouter
from django.urls import path

from .views import *

# router = DefaultRouter()
# router.register()

# urlpatterns = router.urls

app_name = 'collaboration'

urlpatterns = [
    path("", CollaborationPostView.as_view(), name = "create"),                        # POST
    path("search", CollaborationSearchListView.as_view(), name = "search"),                # POST
    path("accept", CollaborateDecisionView.as_view(),name= "accept"),                 # PATCH
    path("response", ResponseCollaborateListView.as_view(), name ="response"), # GET
    path("request", RequestCollaborateListView.as_view(),name = "request"),   # GET
    path("active", ActiveCollaborationListView.as_view(), name = "active"),       # GET
    path("memo", CollaborationUpdateView.as_view(), name = "memo"),                    # PATCH (메모 수정)
    path("<int:collaborateId>", CollaborationDeleteView.as_view(),name= "delete"),   # DELETE
]
