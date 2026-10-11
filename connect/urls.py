from django.urls import path

from connect import views

app_name = 'connect'

urlpatterns = [
    # mentor accounts (email login links)
    path('account/login/', views.login_view, name='login'),
    path('account/login/<str:token>/', views.login_link, name='login_link'),
    path('account/logout/', views.logout_view, name='logout'),
    path('account/', views.dashboard, name='dashboard'),
    path('account/profile/', views.profile_edit, name='profile_edit'),

    # bookings: visitor side (private link) and mentor side
    path('book/<int:mentor_id>/', views.book, name='book'),
    path('book/<int:mentor_id>/slots/', views.slots, name='slots'),
    path('b/<uuid:token>/', views.booking_client, name='booking_client'),
    path('b/<uuid:token>/cancel/', views.booking_client_cancel, name='booking_client_cancel'),
    path('b/<uuid:token>/review/', views.booking_client_review, name='booking_client_review'),
    path('account/bookings/<int:pk>/', views.booking_mentor, name='booking_mentor'),
    path('account/bookings/<int:pk>/<str:action>/', views.booking_mentor_action, name='booking_mentor_action'),

    # projects: owner side and proposer side (private link)
    path('account/projects/<int:pk>/', views.project_manage, name='project_manage'),
    path('account/projects/<int:pk>/close/', views.project_close, name='project_close'),
    path('account/projects/<int:pk>/milestones/', views.milestone_add, name='milestone_add'),
    path('account/milestones/<int:pk>/<str:action>/', views.milestone_update, name='milestone_update'),
    path('account/proposals/<int:pk>/', views.proposal_owner, name='proposal_owner'),
    path('account/proposals/<int:pk>/<str:action>/', views.proposal_action, name='proposal_action'),
    path('account/invite/<int:mentor_id>/', views.invite, name='invite'),
    path('p/<uuid:token>/', views.proposal_client, name='proposal_client'),
    path('p/<uuid:token>/review/', views.proposal_client_review, name='proposal_client_review'),

    # chat threads (JSON)
    path('chat/b/<uuid:ref>/', views.chat, {'kind': 'booking-client'}, name='chat_booking_client'),
    path('chat/booking/<int:ref>/', views.chat, {'kind': 'booking-mentor'}, name='chat_booking_mentor'),
    path('chat/p/<uuid:ref>/', views.chat, {'kind': 'proposal-client'}, name='chat_proposal_client'),
    path('chat/proposal/<int:ref>/', views.chat, {'kind': 'proposal-owner'}, name='chat_proposal_owner'),
]
