# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
# Generated by the OpenERP plugin for Dia !

from openerp import api
from openerp.osv import fields, osv
from datetime import date, datetime, timedelta
import smtplib
import re


class tools_helpdesk_incidencia(osv.osv):
    _name = 'tools.helpdesk.incidencia'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _rec_name = 'codigo'
    
    _columns = {
        'codigo': fields.char('Código', size=10, help="Código de la Incidencia"),
        'solicitante_id': fields.many2one('res.users', string="Solicitante", help='Nombre Completo del Solicitante de la Incidencia'),
        'res_partner_id': fields.related('solicitante_id','res_partner_id', type='many2one', relation='res.partner' , string='Organización'),
        'contexto_nivel1_id': fields.many2one('tools.helpdesk.contexto_nivel1','Aplicación'),
        'contexto_nivel2_id': fields.many2one('tools.helpdesk.contexto_nivel2','Módulo'),
        'contexto_nivel3_id': fields.many2one('tools.helpdesk.contexto_nivel3','Operación'),
        'categoria_incidencia_id': fields.many2one('tools.helpdesk.categoria_incidencia', string="Área de Incidencia"),
        'tipo_incidencia_id': fields.many2one('tools.helpdesk.tipo_incidencia', 'Tipo de Incidencia'),
        'state': fields.selection([('registrado','Registrado'),('leido','Leido'),('asignado','Asignado'),('proceso','En Proceso'),('atendido','Atendido'),('resuelto','Resuelto')], "Status"),
        'observacion_ids': fields.one2many('tools.helpdesk.observacion', 'incidencia_id', string="Observaciones", help='Observaciones de una incidencia'),
        'autorizado': fields.char('Autorizado por:', size=30, help='Colocar el Nombre y Apellido del autorizante'),
        'asignacion' : fields.many2one('res.users', 'Asignado a:'),
    	'denominacion': fields.char('Descripción Corta', size=90),
        'prioridad' : fields.selection([('1','Baja'), ('2', 'Media'),('3','Alta'), ('4','Urgente')],'Prioridad'),
        'fecha_actual' : fields.date('Fecha de la solicitud',  help='Fecha cuando se reporto la incidenciaa', default=datetime.today()),
        'memo':fields.boolean('Memo'),
        'correo':fields.boolean('Correo Electrónico'),
        'llamada':fields.boolean('Llamada Telefonica'),
        'presencial':fields.boolean('Presencial'),
        'gestion':fields.boolean('Gestion Documental'),
        'n_memo':fields.char('Número de Memo'),
        #Para adjuntar los documentos a enviar.
        'adjunto' : fields.one2many('tools.helpdesk.adjuntos', 'adjunto_id', string ="Adjuntos", help='Documentos adicionales, Respaldos Fisicos'),
        #Fin del adjunto
        'descripcion': fields.text('Descripción'),
        'procedimiento': fields.text('Procedimiento en la Solución'),
    	'fecha_creacion': fields.datetime('Fecha de Creación', default=0),
        'fecha_leido': fields.datetime('Fecha de Leido'),
        'fecha_asignado_a': fields.datetime('Fecha Asignado a'),
        'fecha_proceso': fields.datetime('Fecha Proceso'),
        'fecha_atendido': fields.datetime('Fecha Resuelto'),
        'fecha_solucion': fields.datetime('Fecha Cerrado'),
        'dia_creacion': fields.char('Días de Creado'),
        'dia_leido': fields.char('Días Intervalo Creado a Leido'),
        'dia_asignado_a': fields.char('Días Intervalo Leido a Asignado'),
        'dia_proceso': fields.char('Días Intervalo Asignado a Proceso'),
        'dia_atendido': fields.char('Días Intervalo Proceso a Resuelto'),
        'dia_solucion': fields.char('Días Intervalo Resuelto a Cerrado'),
        'retraso': fields.integer('Dias Transcurridos', help="Conteo de dias a pertir de la fecha de entrega", readonly="True", compute="_compute_calculo_dias", store="False")
    }


    @api.onchange('solicitante_id')
    def actualizar_organizacion_solicitante(self):
        self.res_partner_id = self.solicitante_id.res_partner_id.id

    def onchange_solicitante(self, cr, uid, ids):
        return {'value':{'solicitante_id': uid}}

    _order='codigo desc'  #PARA ORDENAR POR CODICO DE MAYOR A MENOR

    def create(self, cr, uid, vals, context=None):
        vals['solicitante_id'] = uid
        vals.update({'codigo':self.pool.get('ir.sequence').get(cr, uid, 'tools.helpdesk.incidencia')}) 
        vals.update({'fecha_creacion':datetime.today()})
        new_id = super(tools_helpdesk_incidencia, self).create(cr, uid, vals, context=None)
        return new_id
    
    # Accion para Botones en el proceso Workflow

    @api.one
    def action_registrado(self):
        self.state='registrado'

    @api.one
    def action_leido(self):
        self.fecha_leido=datetime.today()
        diferencia=self.calcular_dias(self.fecha_creacion, self.fecha_leido)
        self.dia_leido=diferencia.days
        self.state='leido'

    @api.one
    def action_asignado(self):
        if not self.asignacion:
            raise osv.except_osv(('Error'),('Debes llenar el campo: asignado a'))
        self.fecha_asignado_a=datetime.today()
        diferencia=self.calcular_dias(self.fecha_leido, self.fecha_asignado_a)
        self.dia_asignado_a=diferencia.days
        self.state='asignado'

    # PARA ENVIAR E-MAIL            
        cuerpo_mensaje = """Se le ha asignado una tarea en HELP DESK:<br>
        Codigo: %s,<br>
        Asunto: %s,<br>
        Descripcion: %s,<br> """ % (self.codigo, self.denominacion, self.descripcion)
        const_mail = {'email_from' : self.solicitante_id.email,
                      'email_to' : self.asignacion.login,
                      #'partner_ids' : [(0,0,{'res_partner_id':self.asignacion.partner_id, 'mail_message_id': ids_mail})],
                      'subject' : self.denominacion,
                      'body_html' : cuerpo_mensaje}
        ids_mail = self.env['mail.mail'].create(const_mail).send()
        return True 
    # FIN DE EMAIL

    @api.one
    def action_proceso(self):
        self.fecha_proceso=datetime.today()
        diferencia=self.calcular_dias(self.fecha_asignado_a, self.fecha_proceso)
        self.dia_proceso=diferencia.days
        self.state='proceso'

    @api.one
    def action_atendido(self):
        self.fecha_atendido=datetime.today()
        diferencia=self.calcular_dias(self.fecha_proceso, self.fecha_atendido)
        self.dia_atendido=diferencia.days
        self.state='atendido'

    @api.one
    def action_resuelto(self):
        self.fecha_solucion=datetime.today()
        diferencia=self.calcular_dias(self.fecha_atendido, self.fecha_solucion)
        self.dia_solucion=diferencia.days
        self.state='resuelto'
    # PARA ENVIAR E-MAIL AL SOLICITANTE           
        cuerpo_mensaje = """Su INCIDENCIA ya fue resuelta por el departamento HELP DESK:<br>
        Codigo: %s,<br>
        Asunto: %s,<br>
        Descripcion: %s,<br> """ % (self.codigo, self.denominacion, self.descripcion)
        const_mail = {'email_from' : self.asignacion.login,
                      'email_to' : self.solicitante_id.email,                      
                      #'partner_ids' : [(0,0,{'res_partner_id':self.asignacion.partner_id, 'mail_message_id': ids_mail})],
                      'subject' : self.denominacion,
                      'body_html' : cuerpo_mensaje}

        ids_mail = self.env['mail.mail'].create(const_mail).send()
        return True 
    # FIN DE EMAIL AL SOLICITANTE

    #Fin de las acciones en los botones

    # PARA CALCULAR LOS DIAS DE UN PROCESO A OTRO  
    def calcular_dias(self, fecha_primera, fecha_segunda):
        formato_fecha = "%Y-%m-%d"
        fc = datetime.strptime(fecha_primera, "%Y-%m-%d %H:%M:%S")
        fh = datetime.strptime(fecha_segunda, "%Y-%m-%d %H:%M:%S")
        fecha_hoy = datetime.strftime(fh, formato_fecha)
        fecha_creado = datetime.strftime(fc, formato_fecha)
        diferencia = datetime.strptime(fecha_hoy, formato_fecha) - datetime.strptime(fecha_creado, formato_fecha) #fecha_hoy - fecha_creado
        return diferencia
    #FIN DEL CALCULO PARA LOS DIAS DE UN PROCESO A OTRO

    #CALCULA LOS DIAS TRANSCURRIDOS
    @api.depends('fecha_actual')
    def _compute_calculo_dias(self):
        carga = datetime.strptime(self.fecha_actual,'%Y-%m-%d')
        dias = datetime.today() - carga
        self.retraso = dias.days
        return True
    #FIN CALCULOS DE DIAS TRANSCURRIDOS
tools_helpdesk_incidencia()



#class tools_helpdesk_solicitante(osv.osv):
#    """Debería ser una Extensión de la clase hr.employee. Esta clase debe ir en tools.base"""
#    _name = 'tools.helpdesk.solicitante'
#    _rec_name = 'cedula'
#    _columns = {
#        'cedula': fields.integer(string="Cédula", help='Cedula de Identidad del Solicitante'),
#        'nombres': fields.char(string="Nombres", size=60, help='Nombres del Solicitante'),
#        'apellidos': fields.char(string="Apellidos", size=60, help='Apellidos del Solicitante'),
#        'estado_id': fields.many2one('estado', string="Estados", help='Estado donde trabaja el solicitante'),
#        'regional': fields.boolean("Inces Regional"),
#        'rector': fields.boolean("Inces Rector"),
#        'cargo': fields.many2one('tools.base.hr_cargo', string="Cargo", help='Cargo del Solicitante'),
#        'dependencia_direccion_id': fields.many2one('tools.base.dependencia_direccion', string="Dirección"),
#        'dependencia_gerencia_id': fields.many2one('tools.base.dependencia_gerencia', string="Gerencia", help='Gerencia General o Regional a la que pertenece el solicitante'),
#        'dependencia_gerencia_linea_id': fields.many2one('tools.base.dependencia_gerencia_linea', string="Gerencia de Línea", help='Gerencia de Línea a la que pertenece el solicitante (En caso de Gerencia General)'),
#        'dependencia_cfs_id': fields.many2one('tools.base.dependencia_cfs', string="C.F.S.", help='C.F.S al que pertenece el solicitante (En caso de Gerencia Regional)'),
#        'dependencia_division_id': fields.many2one('tools.base.dependencia_division', string="División", help='División a la que pertenece el solicitante'),
#        'dependencia_coordinacion_id': fields.many2one('tools.base.dependencia_coordinacion', string="Coordinación", help='Coordinación a la que pertenece el solicitante'),
#        'email': fields.char(string="Correo Institucional", size=100, help='Correo Electrónico Institucional del solicitante'),
#        'ext_telefono1': fields.char(string="Extensión 1", size=5, help='Extensión Telefónica del Solicitante: Ej: 2066'),
#        'ext_telefono2': fields.char(string="Extensión 2", size=5, help='Extensión Telefónica del Solicitante: Ej: 2066'),
#        'telefono_personal': fields.char(string="Teléfono Personal", size=11, help='Telefóno Personal del Solicitante. Ej: 04261231234'),
#        'incidencia_ids': fields.one2many('tools.helpdesk.incidencia', 'solicitante_id', 'Incidencias Asociadas'),
#    }
#
#    _sql_constraints = [('cedula_solicitante_uniq', 'unique(cedula)', 'Este solicitante ya ha sido registrado en el sistema (cedula repetida)')]
#
#
#
#    @api.constrains('ext_telefono1','telefono_personal')
#    def validar_numerico(self):
#        if not self.ext_telefono1.isdigit():
#            raise osv.except_osv(('Error'),('La extensión debe contender solo numeros'))
#
#        if not self.telefono_personal.isdigit():
#            raise osv.except_osv(('Error'),('El teléfono debe contender solo numeros'))
#    
#    def name_get(self, cr, uid, ids, context=None):
#        res = []
#        solicitantes = self.browse(cr, uid, ids, context)
#        for solicitante in solicitantes:
#            res.append((solicitante.id, str(solicitante.cedula) + ' - ' + solicitante.nombres + ' ' + solicitante.apellidos))
#        return res
#
#    def create(self, cr, uid, vals, context=None):   #esta campo actualiza el registro
#        vals['cedula'] = uid
#        vals['nombres'] = uid
#        vals['apellidos'] = uid
#        result = super(tools.helpdesk.solicitante, self).create(cr, uid, vals, context=context)
#        return result
#tools_helpdesk_solicitante()

class tools_helpdesk_categoria_incidencia(osv.osv):
    """Especificación de la Categoría de la Incidencia,. Ej: Error, Mejora, Nueva, Asistencia"""
    _name = 'tools.helpdesk.categoria_incidencia'
    _rec_name = 'nombre'
    _columns = {
        'codigo': fields.char('Código', size=10, help='Código de esta Categoría de incidencias'),
        'nombre': fields.char('Nombre', size=60, help='Nombre de esta Categoría de Incidencia'),
        'descripcion': fields.text('Descripción'),
        'tipo_incidencia': fields.one2many('tools.helpdesk.tipo_incidencia', 'categoria_incidencia_id', string="tipos de Incidencia", help='Tipos de incidencias que pertenecen a esta Categoría'),
        #'dependencia_id': fields.many2one('tools.base.dependencia_gerencia','Dependencia')
    }
tools_helpdesk_categoria_incidencia()

class tools_helpdesk_tipo_incidencia(osv.osv):
    """Especificación del tipo de Incidencia, depende del área de incidencia. Ej: Sistema X, Sistema Y, Consumibles, Impresora, Soporte Técnico, Correo, Acceso a Internet, Telefonía, Etc"""
    _name = 'tools.helpdesk.tipo_incidencia'
    _rec_name = 'nombre'
    _columns = {
        'codigo': fields.char('Código', size=10, help='Código de este tipo de incidencia'),
        'nombre': fields.char('Nombre', size=60, help='Nombre de este tipo de incidencia'),
        'incidencia_ids': fields.one2many('tools.helpdesk.incidencia', 'tipo_incidencia_id', string="Incidencias", help='Incidencias realizadas para este tipo de incidencia'),
        'categoria_incidencia_id': fields.many2one('tools.helpdesk.categoria_incidencia', string="Categoría de Incidencia", help='Categoría de la Incidencia a la que pertenece este tipo'),
        'descripcion': fields.text('Descripción'),
    }
tools_helpdesk_tipo_incidencia()

class tools_helpdesk_observacion(osv.osv):
    _name = 'tools.helpdesk.observacion'
    _columns = {
        'observacion': fields.text(string="Observación"),
        'state_rel': fields.char(string="Status", size=30, help='Status que tiene la incidencia al momento de hacer la observación'),
        'incidencia_id': fields.many2one('tools.helpdesk.incidencia', help='Relación Inversa del One2many'),
    }
tools_helpdesk_observacion()

class res_users_helpdesk_inherit(osv.osv):
    _inherit= 'res.users'
    _name= 'res.users'
    _columns = {

        'res_partner_id': fields.many2one('res.partner','Organización', help="Organización a la que pertenece el usuario. Necesario para HelpDesk"),
#        'dependencia_id':fields.many2one('tools.base.dependencia_gerencia','Gerencia'),
#        'categoria_incidencia_id':fields.many2one('tools.helpdesk.categoria_incidencia','Area'),
#       'cedula': fields.char(string="Cédula", size=9, help='Cedula de Identidad del Solicitante'),
#        'nombres': fields.char(string="Nombres", size=60, help='Nombres del Solicitante'),
#        'apellidos': fields.char(string="Apellidos", size=60, help='Apellidos del Solicitante'),
#        'estado_id': fields.many2one('estado', string="Estados", help='Estado donde trabaja el solicitante'),
#        'regional': fields.boolean("Inces Regional"),
#        'rector': fields.boolean("Inces Rector"),
#        'cargo': fields.many2one('tools.base.hr_cargo', string="Cargo", help='Cargo del Solicitante'),
#        'dependencia_direccion_id': fields.many2one('tools.base.dependencia_direccion', string="Dirección"),
#       'dependencia_gerencia_id': fields.many2one('tools.base.dependencia_gerencia', string="Gerencia", help='Gerencia General o Regional a la que pertenece el solicitante'),
#        'dependencia_gerencia_linea_id': fields.many2one('tools.base.dependencia_gerencia_linea', string="Gerencia de Línea", help='Gerencia de Línea a la que pertenece el solicitante (En caso de Gerencia General)'),
#        'dependencia_cfs_id': fields.many2one('tools.base.dependencia_cfs', string="C.F.S.", help='C.F.S al que pertenece el solicitante (En caso de Gerencia Regional)'),
#        'dependencia_division_id': fields.many2one('tools.base.dependencia_division', string="División", help='División a la que pertenece el solicitante'),
#        'dependencia_coordinacion_id': fields.many2one('tools.base.dependencia_coordinacion', string="Coordinación", help='Coordinación a la que pertenece el solicitante'),
#        'email': fields.char(string="Correo Institucional", size=100, help='Correo Electrónico Institucional del solicitante'),
#        'ext_telefono1': fields.char(string="Extensión 1", size=5, help='Extensión Telefónica del Solicitante: Ej: 2066'),
#        'ext_telefono2': fields.char(string="Extensión 2", size=5, help='Extensión Telefónica del Solicitante: Ej: 2066'),
#        'telefono_personal': fields.char(string="Teléfono Personal", size=11, help='Telefóno Personal del Solicitante. Ej: 04261231234'),
#        'incidencia_ids': fields.one2many('tools.helpdesk.incidencia', 'solicitante_id', 'Incidencias Asociadas'),
}
#    _sql_constraints = [('cedula_solicitante_uniq', 'unique(cedula)', 'Este solicitante ya ha sido registrado en el sistema (cedula repetida)')]
##    def onchange_validar_caracter(self, uid, cr, ids, nombres):
##    	v={'value':{}}
##    	if nombres:
##    		if not re.math('^[a-zA-Z\D, ]*$', nombres):
##    			v['value']['nombres']=''
##    			v['warning']={'title':'Error', 'message':'ERROR: Este campo no puede llevar numeros ni caraceres especiales: %s' % nombres}
##    		return v
#    def onchange_validar_numero(self, cr, uid, ids, digito):
#        v = {'value':{}}
#        if digito:
#            if not re.match("^[0-9]*$", digito):
#                v['value']['digito']=''
#                v['warning']={'title':"Error", 'message':"ERROR: Este campo no puede llevar letras ni caracteres especiales: %s" % digito }
#            return v	
##    def name_get(self, cr, uid, ids, context=None):
##        res = []
##        solicitantes = self.browse(cr, uid, ids, context)
##        for solicitante in solicitantes:
##            res.append((solicitante.id, +solicitante.cedula + ' - ' + solicitante.nombres + ' ' + solicitante.apellidos))
##        return res
#    def create(self, cr, uid, vals, context=None):   #esta campo actualiza el registro
#        vals['cedula'] = uid
#        vals['nombres'] = uid
#        vals['apellidos'] = uid
#        result = super(res_users_inherit, self).create(cr, uid, vals, context=context)
#        return result


res_users_helpdesk_inherit()

#nueva clase para adjuntar mas de un documento a la incidencia.
class tools_helpdesk_adjuntos(osv.osv):
    _name = 'tools.helpdesk.adjuntos'
    _rec_name = 'nombre'
    _columns = {

        'adjunto' : fields.binary(string="Adjuntos", help='Se suben los archivos adicionales que guardan relacion con el documento'),
        'numero': fields.char(string="Número de adjunto", size=10, help='Numero de adjunto'),
        'nombre': fields.char(string="Nombre del Archivo", size=60, help='Nombre del archivo adjuntado'),
        'observacion' : fields.text(string="Descripción", size=50, help='Breve nota sobre el archivo que se adjunta'),
        'adjunto_id' : fields.many2one('tools.helpdesk.incidencia', 'incidencia'),
}
tools_helpdesk_adjuntos()
#Fin de la clase

#class tools_helpdesk_contexto_nivel1(osv.osv):
#    """Estructura de Dependencias Administrativas"""
#    _name = 'tools.helpdesk.contexto_nivel1'
#    _rec_name = 'nombre'
#    _columns = {
#        'codigo': fields.char(string="Código", size=20, help='Código de la Organización'),
#        'nombre': fields.char(string="Nombre", size=60, help='Nombre de la Organización'),
#        'descripcion': fields.text(string="Descripción", help='Descripción de la Organización'),
#       'contexto_nivel2_ids': fields.one2many('tools.helpdesk.contexto_nivel2', 'contexto_nivel1_id', string="Aplicaciones", help='Aplicaciones Soportadas para esta Organización'),
#    }
#tools_helpdesk_contexto_nivel1()

class tools_helpdesk_contexto_nivel1(osv.osv):
    """Estructura de Dependencias Administrativas"""
    _name = 'tools.helpdesk.contexto_nivel1'
    _rec_name = 'nombre'
    _columns = {
        'codigo': fields.char(string="Código", size=20, help='Código de la Aplicación'),
        'nombre': fields.char(string="Nombre", size=60, help='Nombre de la Aplicación'),
        'descripcion': fields.text(string="Descripción", help='Descripción de la Aplicación'),
        'res_partner_ids': fields.many2many('res.partner','respartner_aplicacion_rel','contexto_nivel1_id','res_partner_id', string="Organización", help='Organización que implementa esta aplicación'),
        'contexto_nivel2_ids': fields.one2many('tools.helpdesk.contexto_nivel2','contexto_nivel1_id', string="Módulo", help='Módulos que pertenecen a esta Aplicación'),
    }    
tools_helpdesk_contexto_nivel1()

class tools_helpdesk_contexto_nivel2(osv.osv):
    _name = 'tools.helpdesk.contexto_nivel2'
    _rec_name = 'nombre'
    _columns = {
        'codigo': fields.char(string="Código", size=20, help='Código del Módulo'),
        'nombre': fields.char(string="Nombre", size=60, help='Nombre del Módulo'),
        'descripcion': fields.text(string="Descripción", help='Descripción del Módulo'),
        'contexto_nivel1_id': fields.many2one('tools.helpdesk.contexto_nivel1', string="Aplicación", help='Aplicación que implementa este módulo'),
        'contexto_nivel3_ids': fields.one2many('tools.helpdesk.contexto_nivel3', 'contexto_nivel2_id', string="Operaciones", help='Operaciones disponibles en este Módulo'),
    }
tools_helpdesk_contexto_nivel2()

class tools_helpdesk_contexto_nivel3(osv.osv):
    _name = 'tools.helpdesk.contexto_nivel3'
    _rec_name = 'nombre'
    _columns = {
        'codigo': fields.char(string="Código", size=20, help='Código de la Operación'),
        'nombre': fields.char(string="Nombre", size=60, help='Nombre de la Operación'),
        'descripcion': fields.text(string="Descripción", help='Descripción de la Operación'),
        'contexto_nivel2_id': fields.many2one('tools.helpdesk.contexto_nivel2', string="Módulo", help='Módulo que implementa esta operación'),
    }
tools_helpdesk_contexto_nivel3()
