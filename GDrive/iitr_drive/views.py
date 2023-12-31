from django.shortcuts import render, redirect, get_object_or_404
from .forms import FolderForm
from django.contrib.auth.decorators import login_required
from .models import Folder, File
from django.urls import reverse
import qrcode
from io import BytesIO
from PIL import Image
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
import uuid

@login_required
def folder_list(request):
    current_user = request.user
    folders = Folder.objects.filter(owner=current_user, linked_in=-1)

    context = {
        'folders': folders,
        'parent_id': -1
    }
    return render(request, 'iitr_drive/folder_list.html', context)


def folder_detail(request, folderid):
    if request.user.is_authenticated:
        folder_user = get_object_or_404(Folder, id=folderid)
        child_folders = Folder.objects.filter(parent_folder=folder_user)
        files = File.objects.filter(folder=folder_user)
        context = {
            'folderid': folderid,
            'files': files,
            'child_folders': child_folders
        }

        if request.method == 'POST':
            # Check if the request contains a file upload
            if 'file' in request.FILES:
                file_user = request.FILES['file']
                file_title = request.POST.get('filetitle')
                if file_title:
                    fileadd = File.objects.create(filetitle=file_title, file=file_user, folder=folder_user)

        return render(request, 'iitr_drive/folder.html', context)
    else:
        return redirect('login')


@csrf_exempt
def add_folder(request):
    if request.method == 'POST':
        folder_name = request.POST.get('f_name')
        discrip = request.POST.get('f_dis')
        parent_id = request.POST.get('f_parent_id')
        
        print(f"Folder Name: {folder_name}")
        print(f"Description: {discrip}")
        print(f"Parent ID: {parent_id}")
        
        if folder_name:  
            owner = request.user
            new_folder = Folder(name=folder_name, description=discrip, owner=owner)
            
            if parent_id != -1:
                try:
                    parent_folder = Folder.objects.get(id=parent_id)
                    new_folder.parent_folder = parent_folder
                except Folder.DoesNotExist:
                    pass  

            new_folder.save()
            print("Folder saved successfully.")
            return redirect('folder_list')
    
    context = {'parent_id': -1}
    return render(request, 'iitr_drive/add_folder.html', {'context':context})


def lauda(request, file_id):
    # Fetch the File object based on file_id
    file_obj = get_object_or_404(File, id=file_id)

    context = {
        'file_obj': file_obj,  # Pass the file object in the context
    }

    return render(request, 'iitr_drive/view_shared_file.html', context)

def generate_qr_code(request, file_id):
    # Fetch the File object based on file_id
    file_obj = get_object_or_404(File, id=file_id)

    # Generate the QR code for the file's URL
    file_url = request.build_absolute_uri(file_obj.file.url)

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=1,
        border=1,
    )
    qr.add_data(file_url)
    qr.make(fit=True)

    # Create Image from QR
    qr_image = qr.make_image(fill_color="black", back_color="white")

    # Prepare the image for rendering in a template
    buffer = BytesIO()
    qr_image.save(buffer, format="PNG")
    qr_image_data = buffer.getvalue()

    # Set the response content type to image/png
    response = HttpResponse(qr_image_data, content_type="image/png")

    # Suggest a filename for the downloaded QR code
    response['Content-Disposition'] = f'attachment; filename="{file_obj.filetitle}_qr.png"'

    return response

@login_required
def delete_file(request, file_id):
    try:
        file = File.objects.get(id=file_id)
        # Check if the user has permission to delete this file
        if file.folder.owner == request.user:
            file.delete()
            return JsonResponse({'success': True, 'message': 'File deleted successfully'})
        else:
            return JsonResponse({'success': False, 'message': 'Permission denied'})
    except File.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'File not found'})