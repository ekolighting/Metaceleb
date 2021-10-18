from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for, make_response, Response
from flask_login import login_required, current_user
from .models import MetaCeleb, Gallery, User
from . import db
import json, datetime, pandas, random, shutil
from werkzeug.utils import secure_filename
from sqlalchemy import or_, desc
from os import walk
from pandas import ExcelWriter
import io, math, os
import pandas as pd
from openpyxl import Workbook
from openpyxl.writer.excel import save_virtual_workbook

BACKUP_PATH = 'website/static/backup/'

Developer = '고재혁'

cj_colors = ['#ff5a00', '#decaa5', '#00bcc8',
             '#ff8347', '#ff898d', '#f2b6ac',
             '#88e6f2', '#009c91', '#cd004d',
             '#790029', '#ffde47', '#7b28f6',
             '#2fe530', '#cce3b9', '#11d8ad',
             '#00780c', '#37481e', '#013c40',
             '#17142f', '#3b1500', '#8d5700'
            ]
columns = {'num': 'NO',
        'title': '제목',
        'genre': '주장르',
        'keyword': '키워드',
        'ref_path': '추천경로',
        'copyright': '저작권',
        'writer': '원작자',
        'copyright_status': '저작권현황',
        'condition': '조건',
        'date_pub': '연재일/출판일',
        'monitored': '모니터링 여부',
        'date_monitored': '모니터링 시점',
        'suggested': '현업제안 여부',
        'date_suggested': '현업제안 시점',
        'story': '줄거리',
        'feedback': '검토의견'}

current_ips = []

prohibit_words = ['None', '']

db_ip_models = [ MetaCeleb, Gallery, User ]

db_dict = {'MetaCeleb': MetaCeleb, 'Gallery' : Gallery, 'User':User }

views = Blueprint('views', __name__)

@views.route('/', methods=['GET', 'POST'])
@login_required
def home():   
    ip_dict = {}
    '''
    for ip_model in db_ip_models:
        ips, total_num, ago = get_db_info(ip_model)
        ip_dict[ip_model] = [ips, total_num, ago]
    '''
    return render_template("home.html", user=current_user, ips = ip_dict)

def get_db_info(ip_model):
    ips = ip_model.query.order_by(desc(ip_model.date)).all()
    total_num = len(ips)
    current_time = datetime.datetime.now()
    date_time_str = ips[0].date
    date_time_obj = datetime.datetime.strptime(date_time_str, "%Y-%m-%d %H:%M:%S")
    ts = current_time - date_time_obj
    mins = int(ts.seconds/60)
    if ts.days:
        ago = str(ts.days) + ' day(s)'
    elif mins > 60:
        hours = int(mins/60)
        ago = str(hours) + ' hour(s)'
    elif mins > 0:
        ago = str(mins) + ' min(s)'
    else:
        ago = str(ts.seconds) + ' seconds'
    return ips, total_num, ago

@views.route('/MetaCeleb/<int:id>', methods=['GET', 'POST'])
@login_required
def img_link(id):
    ip = MetaCeleb.query.filter_by(id=id).first()
    if not ip:
        return 'No images'
    image = Response(ip.img, mimetype = ip.img_mimetype)
    return image

@views.route('/Gallery/<int:id>', methods=['GET', 'POST'])
@login_required
def gallery_link(id):
    ip = Gallery.query.filter_by(id=id).first()
    if not ip:
        return 'No images'
    return ip.img

@views.route('/MetaCeleb', methods=['GET', 'POST'])
@login_required
def show_ip():
    global current_ips
    all_jobs = db.session.query(MetaCeleb.job).distinct()
    this_year = datetime.datetime.now().year
    ips = MetaCeleb.query.order_by(desc(MetaCeleb.id)).all()
    total_num = len(ips)
    return render_template("metaceleb_card.html", user=current_user, ips = ips, total_num = total_num, all_jobs = all_jobs, searched='False', this_year = this_year)

@views.route('/MetaCeleb/Gallery', methods=['GET', 'POST'])
@login_required
def gallery():
    ips = Gallery.query.order_by(desc(Gallery.id)).all()
    return render_template("gallery_flex.html", user=current_user, ips=ips)

@views.route('/MetaCeleb/Gallery_cp', methods=['GET', 'POST'])
@login_required
def gallery_cp():
    ips = Gallery.query.order_by(desc(Gallery.id)).all()
    length = len(ips)
    return render_template("gallery_flex.html", user=current_user, ips=ips, ips_len = length)

@views.route('/MetaCeleb/Gallery_mov', methods=['GET', 'POST'])
@login_required
def gallery_mov():
    ips = Gallery.query.order_by(desc(Gallery.id)).all()
    length = len(ips)
    return render_template("gallery_mov.html", user=current_user, ips=ips, ips_len = length)

@views.route('/adding/Gallery', methods=['GET','POST'])
@login_required
def adding_artwork():
    image_path = 'website/static/images'
    this_year = datetime.datetime.now().year
    ips = Gallery.query.order_by(desc(Gallery.num)).all()
    max_num = get_maxnum(ips)
    all_metaceleb = db.session.query(MetaCeleb.name).distinct()
    if request.method == 'POST':
        ip_exist = False        
        n = request.form.get('num')
        mc_name = request.form.get('metaceleb_name')
        img_title = request.form.get('image_title')
        if not mc_name:
            mc_name = request.form.get('metaceleb_name_1')
        if not mc_name:
            flash('메타셀럽 이름이 없습니다. 확인해주세요!', category='error')
        pic = request.files['pic']
        if not pic:
            flash('이미지가 없습니다. 확인해주세요!', category='error')
            
        file_name = secure_filename(pic.filename)
        img_mimetype = pic.mimetype
        image_path = os.path.join(image_path, mc_name)
        if not os.path.isdir(image_path):
            os.makedirs(image_path)
        image_full_path = os.path.join(image_path, file_name)
        pic.save(image_full_path)
        
        notes = request.form.get('notes')

        if not ip_exist:
            new_ip = Gallery(num=n,
                             metaceleb_name = mc_name,
                             img = image_full_path,
                             img_mimetype = img_mimetype,
                             img_name = img_title,
                             note = notes,
                             user_id=current_user.id, 
                             date = str(datetime.datetime.now()).split('.')[0]
                            )

            db.session.add(new_ip)
            db.session.commit()

            flash('New Artwork is added to Gallery!', category='success')
            return redirect(url_for('views.gallery'))
    return render_template("adding_gallery.html", user=current_user, ips=ips, max_num = max_num, all_metaceleb = all_metaceleb, this_year = this_year)


@views.route('/detail-view/MetaCeleb/<int:id>', methods=['GET','POST'])
@login_required
def deatil_view_metaceleb(id):
    ip_to_update = MetaCeleb.query.get_or_404(id)
    return render_template("detail_view.html", user=current_user, ip = ip_to_update)

@views.route('/detail-view/Gallery/<int:id>', methods=['GET','POST'])
@login_required
def deatil_view_gallery(id):
    ip_to_update = Gallery.query.get_or_404(id)
    return render_template("detail_view.html", user=current_user, ip = ip_to_update)

@views.route('/adding/MetaCeleb', methods=['GET','POST'])
@login_required
def adding():
    this_year = datetime.datetime.now().year
    ips = MetaCeleb.query.order_by(desc(MetaCeleb.num)).all()
    max_num = get_maxnum(ips)
    all_jobs = db.session.query(MetaCeleb.job).distinct()
    all_nats = db.session.query(MetaCeleb.nationality).distinct()
    if request.method == 'POST':
        ip_exist = False        
        n = request.form.get('num')
        na = request.form.get('name')
        re_na = request.form.get('real_name')
        dob_year = request.form.get('dob_year')
        dob_mon = request.form.get('dob_month')
        j = request.form.get('job')
        nat = request.form.get('nationality')
        if not nat:
            nat = request.form.get('nationality_1')
        pic = request.files['pic']
        if not pic:
            flash('이미지가 없습니다. 확인해주세요!', category='error')
            
        img_name = secure_filename(pic.filename)
        img_mimetype = pic.mimetype
        
        if not j:
            j = request.form.get('job_1')

        if len(na) < 1:
            flash('이름이 너무 짧습니다! 확인해주세요!', category='error')
        if MetaCeleb.query.filter_by(name=na).first():
            ip_exist = True
            flash(f'{na} 동일한 메타셀럽이 있습니다! 확인해주세요!', category='error')
        if not ip_exist:
            new_ip = MetaCeleb(num=n,
                               name = na,
                               real_name = re_na,
                               dob = dob_year + '.' + dob_mon,
                               job = j,
                               img = pic.read(),
                               img_mimetype = img_mimetype,
                               img_name = img_name,
                               nationality = nat,
                               user_id=current_user.id, 
                               date = str(datetime.datetime.now()).split('.')[0])
            db.session.add(new_ip)
            db.session.commit()
            
            flash('New MetaCeleb added!', category='success')
            return redirect('/MetaCeleb')
        
    return render_template("adding_ip.html", user=current_user, ips=ips, max_num = max_num, all_jobs = all_jobs, all_nationality = all_nats, this_year = this_year)

def get_maxnum(ips):
    max = 0
    for ip in ips:
        if int(ip.num) > max:
            max = int(ip.num)
    return max+1

@views.route('/delete/MetaCeleb/<int:id>', methods=['GET','POST'])
@login_required
def delete_metaceleb(id):
    ip_to_delete = MetaCeleb.query.get_or_404(id)
    db.session.delete(ip_to_delete)
    db.session.commit()
    print ('MetaCeleb', id ,'was deleted')
    return redirect('/MetaCeleb')

@views.route('/delete/Gallery/<int:id>', methods=['GET','POST'])
@login_required
def delete_gallery(id):
    ip_to_delete = Gallery.query.get_or_404(id)
    db.session.delete(ip_to_delete)
    db.session.commit()
    print ('Gallery', id ,'was deleted')
    return redirect('/MetaCeleb/Gallery')

@views.route('/update/MetaCeleb/<int:id>', methods=['GET', 'POST'])
@login_required
def update_metaceleb(id):
    this_year = datetime.datetime.now().year
    ip_to_update = MetaCeleb.query.get_or_404(id)
    all_jobs = db.session.query(MetaCeleb.job).distinct()
    all_nationality = db.session.query(MetaCeleb.nationality).distinct()
    if request.method == 'POST':
        ip_to_update.num = request.form.get('num')
        ip_to_update.name = request.form.get('name')
        ip_to_update.real_name = request.form.get('real_name')
        ip_to_update.dob_year = request.form.get('dob_year')
        ip_to_updatedob_mon = request.form.get('dob_month')
        ip_to_update.job = request.form.get('job')
        ip_to_update.nationality = request.form.get('nationality')
        if not ip_to_update.nationality:
            ip_to_update.nationality = request.form.get('nationality_1')
        pic = request.files['pic']
        if not pic:
            flash('이미지가 없습니다. 확인해주세요!', category='error')
        ip_to_update.img = pic.read()    
        ip_to_update.img_name = secure_filename(pic.filename)
        ip_to_update.img_mimetype = pic.mimetype
        
        if not ip_to_update.job:
            ip_to_update.job = request.form.get('job_1')

        if len(ip_to_update.name) < 1:
            flash('이름이 너무 짧습니다! 확인해주세요!', category='error')
        else:
            try:
                db.session.commit()
                flash( f'{ip_to_update.__class__.__name__} : {ip_to_update.title} Updated!', category='success')
                return render_template("detail_view.html", user=current_user, ip = ip_to_update)
            except:
                return "There was a problem updating.."
    return render_template("update.html", user=current_user, ip_to_update = ip_to_update, all_jobs = all_jobs, all_nationality = all_nationality,  this_year=this_year)

@views.route('/delete-note', methods=['POST'])
def delete_note():
    note = json.loads(request.data)
    noteId = note['noteId']
    note = WebToonIP.query.get(noteId)
    if note:
        #if note.user_id == current_user.id:
        db.session.delete(note)
        db.session.commit()
    return jsonify({})
