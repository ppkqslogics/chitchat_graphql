from django.shortcuts import render

# Create your views here.
def index(request):
    return render(request, 'index.html', {})


def room(request, current_user,  room_id):
    print(current_user)
    return render(request, 'chat_ui.html', {
        'room_name': room_id,
        'user': current_user
    })
