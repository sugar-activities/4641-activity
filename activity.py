#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2012 Hector Martinez
#                Jorge Ramirez
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

"""Lanzar Activity: a dart game"""

import gtk
import math
import logging
import gobject

from gettext import gettext as _

from sugar.activity import activity
from sugar.graphics.toolbarbox import ToolbarBox
from sugar.activity.widgets import ActivityButton
from sugar.activity.widgets import ActivityToolbox
from sugar.activity.widgets import TitleEntry
from sugar.activity.widgets import StopButton
from sugar.activity.widgets import ShareButton

DELAY = 5
DELTA = 1
WIDTH = 453
HEIGHT = 453
#Array que contiene los puntajes asignados a los sectores de la diana de fondo
POINTS_ARRAY = [6, 13, 4, 18, 1, 20, 5, 12, 9, 14, 11, 8, 16, 7, 19, 3, 17, 2, 15, 10, 6]

class LanzarActivity(activity.Activity):
    """LanzarActivity class as specified in activity.info"""

    def __init__(self, handle):
        """Set up the Lanzar activity."""
        activity.Activity.__init__(self, handle)

        # we do not have collaboration features
        # make the share option insensitive
        self.max_participants = 1

        # toolbar with the new toolbar redesign
        toolbar_box = ToolbarBox()

        activity_button = ActivityButton(self)
        toolbar_box.toolbar.insert(activity_button, 0)
        activity_button.show()

        separator = gtk.SeparatorToolItem()
        separator.props.draw = False
        separator.set_expand(True)
        toolbar_box.toolbar.insert(separator, -1)
        separator.show()

        stop_button = StopButton(self)
        toolbar_box.toolbar.insert(stop_button, -1)
        stop_button.show()

        # variables de configuracion y control del juego
        self.DELTA_X = DELTA
        self.DELTA_Y = DELTA
        self._score = 0

        # Variable global que ira indicando el "indice" de pixel donde dibujar
        # la linea vertical
        self._x = 0

        # Variable global que contendra el "indice" de pixel donde el usuario
        # presiono alguna tecla para detenerlo. El valor inicial -1 indica que
        # todavia no se ha presionado una tecla para la linea vertical
        self._selected_x = -1

        # Variable global que ira indicando el "indice" de pixel donde dibujar
        # la linea horizontal
        self._y = 0

        # Variable global que contendra el "indice" de pixel donde el usuario
        # presiono alguna tecla para detenerlo. El valor inicial -1 indica que
        # todavia no se ha presionado una tecla para la linea horizontal
        self._selected_y = -1

        self.drawing_area = gtk.DrawingArea()
        self.drawing_area.set_size_request(WIDTH, HEIGHT)

        self.pixbuf = gtk.gdk.pixbuf_new_from_file('images/dartboard.png')
        self.dart_pixbuf = gtk.gdk.pixbuf_new_from_file('images/dart.png') 

        self.drawing_area.connect('configure_event', self.__configure_cb)
        self.drawing_area.connect('expose-event', self.__expose_cb)
        self.connect('key-press-event', self.__key_press_cb, self.drawing_area)
        
        # tablero
        board_box = gtk.Alignment()
        board_box.add(self.drawing_area)
        board_box.set_padding(0, 0, 144, 0)
        self.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color())

        # puntaje
        score_str = gtk.Label()
        score_str.set_markup("<span foreground='white' size='xx-large'><b>%s</b></span>" % _("Score"))
        self.score_text = gtk.Label()
        self.score_text_tmpl = "<span foreground='white' size='xx-large'>%s</span>" 
        self.score_text.set_markup(self.score_text_tmpl % self._score)
        score_box = gtk.VBox()
        score_box.pack_start(score_str, expand=False, fill=False)
        score_box.pack_start(self.score_text, expand=False, fill=False)
        score_align = gtk.Alignment()
        score_align.set_padding(100, 0, 0, 0)
        score_align.add(score_box)

        # box principal
        main_box = gtk.HBox()
        main_box.add(board_box)
        main_box.add(score_align)
        
        gobject.timeout_add(DELAY, self.__move_vertical_line, self.drawing_area)

        self.set_canvas(main_box)
        self.set_toolbar_box(toolbar_box)
        
        toolbar_box.show()
        main_box.show_all()

    def __configure_cb(self, drawing_area, data=None):
        x, y, width, height = drawing_area.get_allocation()

        canvas = drawing_area.window
        self.pixmap = gtk.gdk.Pixmap(canvas, width, height)
        return True

    def __expose_cb(self, drawing_area, data=None):
        x, y, width, height = data.area

        context = drawing_area.get_style().fg_gc[gtk.STATE_NORMAL]

        canvas = drawing_area.window
        canvas.draw_drawable(context, self.pixmap, x, y, x, y, width, height)
        return False

    def draw_background(self, drawing_area):
        #Utilizado para dibujar objetos en el pixmap
        cr = self.pixmap.cairo_create()
        
        # Dibujar inicialmente un fondo negro
        cr.set_source_rgb(0, 0, 0)
        rectangle = gtk.gdk.Rectangle(0, 0, WIDTH, HEIGHT)
        rectangle = cr.rectangle(rectangle)
        drawing_area.queue_draw() 
        cr.fill()

        # Dibujar la diana sobre el fondo negro
        self.pixmap.draw_pixbuf(None, self.pixbuf, 0, 0, 0, 0, -1, -1,
                                gtk.gdk.RGB_DITHER_NONE, 0, 0)

    def draw_line(self, drawing_area, orientation, line_index):
        #Utilizado para dibujar objetos en el pixmap
        cr = self.pixmap.cairo_create()

        # Dibujar una linea que ocupe toda la pantalla y sea de
        # color blanco para contrastarlo con la diana
        cr.set_source_rgb(255, 255, 255)

        if orientation == "VERTICAL":
            rectangle = gtk.gdk.Rectangle(line_index, 0, 1, HEIGHT)
        else:
            rectangle = gtk.gdk.Rectangle(0, line_index, WIDTH, 1)

        rectangle = cr.rectangle(rectangle)
        drawing_area.queue_draw() 
        cr.fill()
        
    def __move_vertical_line(self, drawing_area):
        #Dibujar el fondo sobre el cual movemos las lineas, si aun no hemos
        #presionado un boton para dejar la linea vertical en una coordenada dada
        if self._selected_x < 0:
            self.draw_background(drawing_area)
        
        # Mover el indice x para que aparente movimiento
        self._x += self.DELTA_X;
        if self._x > WIDTH:
            self.DELTA_X *= -1
        elif self._x < 0:
            self.DELTA_X *= -1

        # Dibujar una linea vertical en la x correspondiente
        self.draw_line(drawing_area, "VERTICAL", self._x)
        
        # Si aun no se selecciono un indice para x, seguir permitiendo invocar
        # al timer. Caso contrario, retornar False para evitar mas invocaciones
        if self._selected_x < 0:
            return True
        else:
            return False
    
    def __move_horizontal_line(self, drawing_area):
        #Dibujar el fondo sobre el cual movemos las lineas
        self.draw_background(drawing_area)

        # Como la linea vertical ya se detuvo para poder mover la linea 
        # horizontal, dibujar la linea vertical en la x seleccionada
        self.draw_line(drawing_area, "VERTICAL", self._selected_x)

        # Mover el indice y para que aparente movimiento
        self._y += self.DELTA_Y;
        if self._y > HEIGHT:
            self.DELTA_Y *= -1
        elif self._y < 0:
            self.DELTA_Y *= -1

        # Dibujar una linea horizontal en la y correspondiente
        self.draw_line(drawing_area, "HORIZONTAL", self._y)

        # Si aun no se selecciono un indice para y, seguir permitiendo invocar
        # al timer. Caso contrario, retornar False para evitar mas invocaciones
        if self._selected_y < 0:
            return True
        else:
            return False

    def __key_press_cb(self, window, event, drawing_area):
        # Al presionar cualquier tecla, determinar la accion a tomar, de 
        # acuerdo al estado de las lineas.
        if self._selected_x == -1:
            self._selected_x = self._x
            gobject.timeout_add(DELAY, self.__move_horizontal_line, drawing_area)            
        elif self._selected_y == -1:
            self._selected_y = self._y
            gobject.timeout_add(DELAY, self.__draw_dart, drawing_area)
        else:
            self.restart_game(drawing_area)

    def __draw_dart(self, drawing_area):
        """
        Dibuja el dardo una vez que se obtuvieron X e Y. Ademas muestra
        el puntaje obtenido.
        """
        x = self._selected_x - 24 # para centrar la imagen
        y = self._selected_y - 24
        
        self.score = self.compute_score(self._selected_x, self._selected_y)
        self.score_text.set_markup(self.score_text_tmpl % self.score)

        self.draw_background(drawing_area)
        self.draw_line(drawing_area, "HORIZONTAL", self._selected_y)
        self.draw_line(drawing_area, "VERTICAL", self._selected_x)
        self.pixmap.draw_pixbuf(None, self.dart_pixbuf, 0, 0, x, y, -1, -1,
                                gtk.gdk.RGB_DITHER_NONE, 0, 0)
        
    def restart_game(self, drawing_area):
        self._x = self._y = 0
        self._selected_x = self._selected_y = -1 
        gobject.timeout_add(DELAY, self.__move_vertical_line, drawing_area)

    def compute_score(self, x, y):
        """ 
        Calcula el puntaje en base a las coordenadas X e Y dadas como parametro.
        """
        #Variables para el calculo del puntaje
        score = 0
        distance = 0
        rho = 0
        option_index = 0

        #Variables dependientes de la imagen de fondo (dartboard.png)
        center_x = 226
        center_y = 227
        radius_bullseye = 7
        radius_bull = 16
        radius_begin_triple = 98
        radius_end_triple = 107
        radius_begin_double = 161
        radius_end_double = 170
        
        #Calculo de la distancia euclidea del punto "seleccionado" respecto al centro
        distance = math.sqrt(math.pow(abs(x - center_x),2) + math.pow(abs(y - center_y),2))

        #Transformar x e y para que origen de coordenadas esten en el centro del bullseye
        displaced_x = x - center_x
        displaced_y = center_y - y

        #Obtener el angulo respecto al eje de las abscisas
        rho = math.degrees(math.atan2(displaced_y, displaced_x))
        if rho < 0:
            rho = 360 + rho
            
        #Obtener indice de sector (que tiene asignado un puntaje en el tablero)
        #Existen 20 puntajes posibles, en un circulo de 360 grados, por lo que
        #cada puntaje "ocupa" 360/20=18 grados, y los sectores de puntajes estan
        #desplazados 9 grados, por lo que matematicamente se puede hallarlo 
        #segun la ecuacion que sigue
        point_index = int(math.floor(((rho - 9) / 18) + 1))
        
        #Calculo exacto de puntaje de acuerdo a reglas de juego de dardos
        score = POINTS_ARRAY[point_index]
        if distance < radius_bullseye:
            score = 50
        elif distance < radius_bull:
            score = 25
        elif distance >= radius_begin_triple and distance <= radius_end_triple:
            score = score * 3
        elif distance >= radius_begin_double and distance <= radius_end_double:
            score = score * 2
        elif distance > radius_end_double:
            score = 0
        
        #Impresiones para depurar valores utiles en el calculo de puntaje
        logging.debug("X: " + str(x) + " Y: " + str(y))
        logging.debug("__X: " + str(displaced_x) + " __Y: " + str(displaced_y))
        logging.debug("DISTANCE: "+str(distance) + " RHO: "+str(rho))
        logging.debug("SCORE: "+str(int(score))+" SCORE2: "+str(POINTS_ARRAY[point_index]))

        return int(score)
        
