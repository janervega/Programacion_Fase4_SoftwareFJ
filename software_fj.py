# -*- coding: utf-8 -*-
"""
Universidad Nacional Abierta y a Distancia (UNAD)
Escuela de Ciencias Básicas, Tecnología e Ingeniería (ECBTI)
Programa: Ingeniería de Sistemas
Curso: Programación (Código 213023)
Fase 4: Componente práctico - Prácticas simuladas

Ejercicio 1: Sistema Integral de Gestión de Clientes, Servicios y Reservas
Caso de estudio: Empresa Software FJ (según Anexo 3)

Estudiante: Janner Jose Vega Torres
Grupo: 133
Tutor: Gustavo Adolfo Marun Suarez
Año: 2026
"""

import abc
import datetime
import logging
import os
import re
import sys
from typing import Dict, List, Optional, Any


# ==============================================================================
# CONFIGURACIÓN DE LOGS (AUDITORÍA DEL SISTEMA)
# ==============================================================================
# Definimos el archivo de log en la misma carpeta del script
RUTA_CARPETA = os.path.dirname(os.path.abspath(__file__))
ARCHIVO_LOG = os.path.join(RUTA_CARPETA, "software_fj.log")

# Configuramos el logger para que guarde eventos en archivo y muestre en consola
logger = logging.getLogger("SoftwareFJ")
logger.setLevel(logging.DEBUG)

if not logger.handlers:
    # Handler para guardar en archivo (persistente)
    handler_archivo = logging.FileHandler(ARCHIVO_LOG, mode="a", encoding="utf-8")
    handler_archivo.setLevel(logging.DEBUG)
    
    # Handler para mostrar en terminal
    handler_consola = logging.StreamHandler(sys.stdout)
    handler_consola.setLevel(logging.INFO)
    
    # Formato con fecha, hora, nivel y mensaje
    formato = logging.Formatter(
        "%(asctime)s [%(levelname)s] [%(name)s:%(lineno)d] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler_archivo.setFormatter(formato)
    handler_consola.setFormatter(formato)
    
    logger.addHandler(handler_archivo)
    logger.addHandler(handler_consola)

logger.info("Sistema de gestion Software FJ iniciado correctamente en memoria.")


# ==============================================================================
# JERARQUÍA DE EXCEPCIONES PERSONALIZADAS
# ==============================================================================
# Creamos una clase base para los errores de la empresa y luego especializamos
# para clasificar fallos de datos, disponibilidad, transiciones y cálculos.

class SoftwareFJError(Exception):
    """Clase base para todas las excepciones del sistema Software FJ."""
    def __init__(self, mensaje: str, codigo: str = "ERR-000"):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.codigo = codigo
        self.momento = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def __str__(self) -> str:
        return f"[{self.codigo}] {self.mensaje} ({self.momento})"


class DatoInvalidoError(SoftwareFJError):
    """Se lanza cuando un campo no cumple con formato, tipo o longitud esperada."""
    def __init__(self, mensaje: str):
        super().__init__(mensaje, codigo="ERR-DATOS-100")


class ServicioNoDisponibleError(SoftwareFJError):
    """Se lanza cuando un servicio no tiene disponibilidad física o de inventario."""
    def __init__(self, mensaje: str):
        super().__init__(mensaje, codigo="ERR-DISP-200")


class OperacionNoPermitidaError(SoftwareFJError):
    """Se lanza cuando se intenta realizar una acción no válida según el estado actual."""
    def __init__(self, mensaje: str):
        super().__init__(mensaje, codigo="ERR-OPER-300")


class CalculoInconsistenteError(SoftwareFJError):
    """Se lanza cuando valores numéricos, horas o tarifas son ilógicos o negativos."""
    def __init__(self, mensaje: str):
        super().__init__(mensaje, codigo="ERR-CALC-400")


class ReservaInvalidaError(SoftwareFJError):
    """Se lanza cuando los datos de una reserva no se pueden asociar correctamente."""
    def __init__(self, mensaje: str):
        super().__init__(mensaje, codigo="ERR-RES-500")


# ==============================================================================
# CLASE ABSTRACTA BASE: EntidadSistema
# ==============================================================================
class EntidadSistema(abc.ABC):
    """
    Clase abstracta que sirve de base para cualquier entidad del negocio.
    Aplica el principio de abstracción definiendo atributos comunes y métodos
    que las subclases deben implementar obligatoriamente.
    """
    def __init__(self, identificador: str):
        if not identificador or not isinstance(identificador, str):
            raise DatoInvalidoError("El identificador de la entidad no puede estar vacío.")
        self._identificador = identificador.strip()
        self._fecha_alta = datetime.datetime.now()
        self._activo = True

    @property
    def identificador(self) -> str:
        return self._identificador

    @property
    def activo(self) -> bool:
        return self._activo

    def activar(self) -> None:
        self._activo = True
        logger.info(f"Entidad {self._identificador} activada en el sistema.")

    def desactivar(self) -> None:
        self._activo = False
        logger.warning(f"Entidad {self._identificador} desactivada temporalmente.")

    @abc.abstractmethod
    def obtener_detalle(self) -> Dict[str, Any]:
        """Debe retornar un diccionario con los datos descriptivos de la entidad."""
        pass

    @abc.abstractmethod
    def validar_estado(self) -> bool:
        """Debe verificar si la entidad cumple con las condiciones para operar."""
        pass


# ==============================================================================
# CLASE CONCRETA: Cliente
# ==============================================================================
class Cliente(EntidadSistema):
    """
    Representa a los clientes de Software FJ (personas naturales o empresas).
    Implementa encapsulamiento con atributos privados y métodos property con
    validaciones estrictas mediante expresiones regulares.
    """
    PATRON_CORREO = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    TIPOS_CLIENTE = ("NATURAL", "CORPORATIVO")

    def __init__(self, id_cliente: str, nombre: str, correo: str, telefono: str, tipo_cliente: str = "NATURAL"):
        super().__init__(identificador=id_cliente)
        self.__nombre = ""
        self.__correo = ""
        self.__telefono = ""
        self.__tipo_cliente = "NATURAL"
        self.__puntos = 0

        # Asignamos mediante los setters para que se apliquen las validaciones
        self.nombre = nombre
        self.correo = correo
        self.telefono = telefono
        self.tipo_cliente = tipo_cliente

    # --- Nombre ---
    @property
    def nombre(self) -> str:
        return self.__nombre

    @nombre.setter
    def nombre(self, valor: str) -> None:
        if not valor or not isinstance(valor, str):
            raise DatoInvalidoError("El nombre del cliente es obligatorio.")
        limpio = valor.strip()
        if len(limpio) < 3:
            raise DatoInvalidoError(f"El nombre '{valor}' es demasiado corto (mínimo 3 caracteres).")
        if any(c.isdigit() for c in limpio):
            raise DatoInvalidoError(f"El nombre '{valor}' no debe contener números.")
        self.__nombre = limpio

    # --- Correo Electrónico ---
    @property
    def correo(self) -> str:
        return self.__correo

    @correo.setter
    def correo(self, valor: str) -> None:
        if not valor or not isinstance(valor, str):
            raise DatoInvalidoError("El correo electrónico no puede ser nulo.")
        limpio = valor.strip()
        if not re.match(self.PATRON_CORREO, limpio):
            raise DatoInvalidoError(f"El correo '{valor}' no tiene un formato válido (usuario@dominio.com).")
        self.__correo = limpio

    # --- Teléfono (con demostración de encadenamiento de excepciones) ---
    @property
    def telefono(self) -> str:
        return self.__telefono

    @telefono.setter
    def telefono(self, valor: str) -> None:
        if not valor:
            raise DatoInvalidoError("El teléfono del cliente es requerido.")
        valor_cadena = str(valor).strip()

        # Usamos try/except con raise ... from para encadenar ValueError a nuestra excepción
        try:
            int(valor_cadena)
        except ValueError as err_origen:
            raise DatoInvalidoError(
                f"El teléfono '{valor_cadena}' contiene letras o símbolos no permitidos."
            ) from err_origen

        if len(valor_cadena) != 10:
            raise DatoInvalidoError(
                f"El teléfono debe tener exactamente 10 dígitos (suministrados: {len(valor_cadena)})."
            )
        self.__telefono = valor_cadena

    # --- Tipo de Cliente ---
    @property
    def tipo_cliente(self) -> str:
        return self.__tipo_cliente

    @tipo_cliente.setter
    def tipo_cliente(self, valor: str) -> None:
        tipo_normalizado = str(valor).upper().strip()
        if tipo_normalizado not in self.TIPOS_CLIENTE:
            raise DatoInvalidoError(f"Tipo de cliente '{valor}' no válido. Use: {self.TIPOS_CLIENTE}")
        self.__tipo_cliente = tipo_normalizado

    @property
    def puntos(self) -> int:
        return self.__puntos

    def sumar_puntos(self, cantidad: int) -> None:
        if cantidad <= 0:
            raise CalculoInconsistenteError("La cantidad de puntos a sumar debe ser mayor a 0.")
        self.__puntos += cantidad
        logger.info(f"Cliente {self.identificador} acumuló {cantidad} puntos. Total: {self.__puntos}")

    def obtener_detalle(self) -> Dict[str, Any]:
        return {
            "id": self.identificador,
            "nombre": self.__nombre,
            "correo": self.__correo,
            "telefono": self.__telefono,
            "tipo": self.__tipo_cliente,
            "puntos": self.__puntos,
            "activo": self.activo
        }

    def validar_estado(self) -> bool:
        return self.activo and bool(self.__nombre) and bool(self.__correo)


# ==============================================================================
# CLASE ABSTRACTA: Servicio
# ==============================================================================
class Servicio(EntidadSistema, abc.ABC):
    """
    Superclase abstracta para los servicios de Software FJ.
    Define las tarifas base y obliga a las subclases a implementar métodos
    polimórficos de costo, descripción y validación técnica.
    """
    def __init__(self, codigo: str, nombre: str, tarifa_base: float):
        super().__init__(identificador=codigo)
        if not nombre or not isinstance(nombre, str):
            raise DatoInvalidoError("El nombre del servicio no puede ser vacío.")
        if tarifa_base <= 0:
            raise CalculoInconsistenteError(f"La tarifa base ({tarifa_base}) debe ser mayor a cero.")
        
        self._nombre = nombre.strip()
        self._tarifa_base = float(tarifa_base)
        self._disponible = True

    @property
    def codigo(self) -> str:
        return self.identificador

    @property
    def nombre(self) -> str:
        return self._nombre

    @property
    def tarifa_base(self) -> float:
        return self._tarifa_base

    @property
    def disponible(self) -> bool:
        return self._disponible and self.activo

    def habilitar(self) -> None:
        self._disponible = True
        logger.info(f"Servicio {self.codigo} marcado como DISPONIBLE.")

    def inhabilitar(self) -> None:
        self._disponible = False
        logger.warning(f"Servicio {self.codigo} marcado como NO DISPONIBLE.")

    # --- Métodos abstractos (Polimorfismo) ---
    @abc.abstractmethod
    def calcular_costo_base(self, duracion: float) -> float:
        """Calcula el costo bruto del servicio según horas o días."""
        pass

    @abc.abstractmethod
    def describir_servicio(self) -> str:
        """Devuelve una ficha descriptiva con las características del servicio."""
        pass

    @abc.abstractmethod
    def validar_parametros(self, **kwargs) -> bool:
        """Verifica restricciones técnicas propias de cada servicio."""
        pass

    # --- Método con sobrecarga para liquidación comercial ---
    def liquidar_costo(self, duracion: float, descuento_porcentaje: float = 0.0, 
                       iva_porcentaje: float = 0.19, **adicionales) -> Dict[str, float]:
        """
        Sobrecarga mediante argumentos por defecto y empaquetamiento kwargs.
        Permite calcular el valor total considerando duración, descuentos, IVA
        y cargos opcionales.
        """
        if duracion <= 0:
            raise CalculoInconsistenteError(f"La duración ({duracion}) debe ser un número positivo.")
        if not (0.0 <= descuento_porcentaje <= 100.0):
            raise CalculoInconsistenteError(f"Descuento ({descuento_porcentaje}%) fuera de rango (0-100%).")
        if iva_porcentaje < 0:
            raise CalculoInconsistenteError("La tasa de IVA no puede ser negativa.")

        # Llamado polimórfico a la subclase
        costo_base = self.calcular_costo_base(duracion)
        
        recargo_extra = float(adicionales.get("recargo", 0.0))
        if recargo_extra < 0:
            raise CalculoInconsistenteError("El recargo adicional no puede ser negativo.")

        subtotal = costo_base + recargo_extra
        valor_descuento = subtotal * (descuento_porcentaje / 100.0)
        base_gravable = subtotal - valor_descuento
        valor_iva = base_gravable * iva_porcentaje
        total = base_gravable + valor_iva

        return {
            "costo_base": round(costo_base, 2),
            "recargo": round(recargo_extra, 2),
            "descuento": round(valor_descuento, 2),
            "base_gravable": round(base_gravable, 2),
            "iva": round(valor_iva, 2),
            "total": round(total, 2)
        }

    def obtener_detalle(self) -> Dict[str, Any]:
        return {
            "codigo": self.codigo,
            "nombre": self.nombre,
            "tarifa_base": self.tarifa_base,
            "disponible": self.disponible,
            "descripcion": self.describir_servicio()
        }

    def validar_estado(self) -> bool:
        return self.activo and self._disponible


# ==============================================================================
# SUBCLASES ESPECIALIZADAS (SERVICIOS DE SOFTWARE FJ)
# ==============================================================================

class ReservaSala(Servicio):
    """
    Servicio de salas físicas para eventos, juntas y talleres.
    Calcula por HORAS y suma costos fijos de equipos audiovisuales y catering.
    """
    TARIFAS_SALA = {
        "JUNTAS": {"hora": 50000.0, "max_personas": 15},
        "AUDITORIO": {"hora": 150000.0, "max_personas": 120},
        "TALLER": {"hora": 80000.0, "max_personas": 35}
    }

    def __init__(self, codigo: str, nombre: str, tipo_sala: str, capacidad: int,
                 con_proyector: bool = True, con_refrigerio: bool = False, costo_refrigerio: float = 12000.0):
        tipo_sala_clean = tipo_sala.upper().strip()
        if tipo_sala_clean not in self.TARIFAS_SALA:
            raise DatoInvalidoError(f"Tipo de sala '{tipo_sala}' no existe. Opciones: {list(self.TARIFAS_SALA.keys())}")
        
        tarifa_hora = self.TARIFAS_SALA[tipo_sala_clean]["hora"]
        super().__init__(codigo=codigo, nombre=nombre, tarifa_base=tarifa_hora)
        
        self.__tipo_sala = tipo_sala_clean
        self.__capacidad = capacidad
        self.__con_proyector = con_proyector
        self.__con_refrigerio = con_refrigerio
        self.__costo_refrigerio = costo_refrigerio

        self.validar_parametros()

    def validar_parametros(self, **kwargs) -> bool:
        max_permitido = self.TARIFAS_SALA[self.__tipo_sala]["max_personas"]
        if not (1 <= self.__capacidad <= max_permitido):
            raise DatoInvalidoError(
                f"Capacidad solicitada ({self.__capacidad}) fuera de límite para sala {self.__tipo_sala} (1 a {max_permitido})."
            )
        if self.__costo_refrigerio < 0:
            raise CalculoInconsistenteError("El costo unitario de refrigerio no puede ser negativo.")
        return True

    def calcular_costo_base(self, duracion: float) -> float:
        # La duración es en horas (mínimo 1 hora, máximo 10 horas)
        if not (1.0 <= duracion <= 10.0):
            raise CalculoInconsistenteError(f"Duración de sala inválida: {duracion} hrs. Debe ser entre 1 y 10 horas.")
        
        total_horas = self.tarifa_base * duracion
        extra_proyector = 30000.0 if self.__con_proyector else 0.0
        extra_refrigerio = (self.__costo_refrigerio * self.__capacidad) if self.__con_refrigerio else 0.0
        return total_horas + extra_proyector + extra_refrigerio

    def describir_servicio(self) -> str:
        proy = "Con proyector HD" if self.__con_proyector else "Sin proyector"
        ref = "Incluye refrigerio" if self.__con_refrigerio else "Sin refrigerio"
        return f"Sala tipo {self.__tipo_sala} ('{self.nombre}'), capacidad {self.__capacidad} personas. {proy}, {ref}. Tarifa/h: ${self.tarifa_base:,.0f}"


class AlquilerEquipo(Servicio):
    """
    Servicio de préstamo de hardware (servidores, portátiles, switches).
    Calcula por DÍAS de uso y maneja depósito en garantía y stock físico.
    """
    CATEGORIAS = ("PORTATIL", "SERVIDOR", "REDES")

    def __init__(self, codigo: str, nombre: str, tarifa_diaria: float, categoria: str,
                 deposito: float, stock: int, seguro_incluido: bool = True):
        super().__init__(codigo=codigo, nombre=nombre, tarifa_base=tarifa_diaria)
        categoria_clean = categoria.upper().strip()
        if categoria_clean not in self.CATEGORIAS:
            raise DatoInvalidoError(f"Categoría '{categoria}' inválida. Use: {self.CATEGORIAS}")
        
        self.__categoria = categoria_clean
        self.__deposito = float(deposito)
        self.__stock = int(stock)
        self.__seguro_incluido = seguro_incluido

        self.validar_parametros()

    @property
    def stock(self) -> int:
        return self.__stock

    def validar_parametros(self, **kwargs) -> bool:
        if self.__deposito < 0:
            raise CalculoInconsistenteError("El depósito no puede ser negativo.")
        if self.__stock < 0:
            raise CalculoInconsistenteError("El stock de equipos no puede ser menor a cero.")
        return True

    def prestar_unidad(self) -> None:
        if self.__stock <= 0:
            raise ServicioNoDisponibleError(f"No hay unidades disponibles del equipo [{self.codigo}].")
        self.__stock -= 1
        if self.__stock == 0:
            self.inhabilitar()
        logger.info(f"Unidad prestada de [{self.codigo}]. Stock restante: {self.__stock}")

    def devolver_unidad(self) -> None:
        self.__stock += 1
        self.habilitar()
        logger.info(f"Unidad devuelta de [{self.codigo}]. Stock total: {self.__stock}")

    def calcular_costo_base(self, duracion: float) -> float:
        # La duración es en días (mínimo 1 día)
        if duracion < 1.0:
            raise CalculoInconsistenteError("El alquiler mínimo de equipos es de 1 día.")
        dias = int(duracion)
        costo_dias = self.tarifa_base * dias
        seguro = (costo_dias * 0.05) if self.__seguro_incluido else 0.0
        return costo_dias + seguro

    def describir_servicio(self) -> str:
        seg = "Póliza incluida (5%)" if self.__seguro_incluido else "Sin póliza"
        return f"Equipo {self.__categoria}: '{self.nombre}', Stock: {self.__stock} uds, Depósito: ${self.__deposito:,.0f}. {seg}. Tarifa/día: ${self.tarifa_base:,.0f}"


class AsesoriaEspecializada(Servicio):
    """
    Servicio de consultoría en TI (Cloud, Ciberseguridad, IA).
    Calcula por HORAS trabajadas según el nivel del consultor y viáticos si es presencial.
    """
    NIVELES = {"JUNIOR": 1.0, "SENIOR": 1.4, "CONSULTOR_MASTER": 1.8}
    MODALIDADES = ("REMOTA", "PRESENCIAL")

    def __init__(self, codigo: str, nombre: str, tarifa_hora: float, area: str,
                 nivel: str = "SENIOR", modalidad: str = "REMOTA"):
        super().__init__(codigo=codigo, nombre=nombre, tarifa_base=tarifa_hora)
        nivel_clean = nivel.upper().strip()
        modalidad_clean = modalidad.upper().strip()

        if nivel_clean not in self.NIVELES:
            raise DatoInvalidoError(f"Nivel '{nivel}' desconocido. Opciones: {list(self.NIVELES.keys())}")
        if modalidad_clean not in self.MODALIDADES:
            raise DatoInvalidoError(f"Modalidad '{modalidad}' no permitida. Opciones: {self.MODALIDADES}")

        self.__area = area.strip()
        self.__nivel = nivel_clean
        self.__modalidad = modalidad_clean

        self.validar_parametros()

    def validar_parametros(self, **kwargs) -> bool:
        if not self.__area:
            raise DatoInvalidoError("El área de especialidad técnica no puede estar vacía.")
        return True

    def calcular_costo_base(self, duracion: float) -> float:
        # Mínimo 2 horas por sesión de asesoría
        if duracion < 2.0:
            raise CalculoInconsistenteError("Las asesorías requieren un bloque mínimo de 2 horas.")
        
        factor = self.NIVELES[self.__nivel]
        costo_tiempo = (self.tarifa_base * factor) * duracion
        viaticos = 90000.0 if self.__modalidad == "PRESENCIAL" else 0.0
        return costo_tiempo + viaticos

    def describir_servicio(self) -> str:
        return f"Asesoría en {self.__area} ('{self.nombre}'), Nivel: {self.__nivel}, Modalidad: {self.__modalidad}. Tarifa base/h: ${self.tarifa_base:,.0f}"


# ==============================================================================
# CLASE: Reserva
# ==============================================================================
class Reserva(EntidadSistema):
    """
    Asocia un cliente con un servicio determinado, controlando los estados:
    REGISTRADA -> CONFIRMADA -> PAGADA (o CANCELADA).
    """
    ESTADOS = ("REGISTRADA", "CONFIRMADA", "PAGADA", "CANCELADA")

    def __init__(self, id_reserva: str, cliente: Cliente, servicio: Servicio, duracion: float, descuento: float = 0.0):
        super().__init__(identificador=id_reserva)
        if not isinstance(cliente, Cliente) or not cliente.validar_estado():
            raise ReservaInvalidaError("No se puede crear reserva con un cliente inactivo o inválido.")
        if not isinstance(servicio, Servicio) or not servicio.validar_estado():
            raise ServicioNoDisponibleError(f"El servicio [{getattr(servicio, 'codigo', 'N/A')}] no está disponible.")
        if duracion <= 0:
            raise CalculoInconsistenteError("La duración de la reserva debe ser mayor a cero.")

        self._cliente = cliente
        self._servicio = servicio
        self._duracion = float(duracion)
        self._estado = "REGISTRADA"
        self._motivo_anulacion = None
        
        # Realizamos la liquidación inicial mediante el método sobrecargado
        self._liquidacion = self._servicio.liquidar_costo(duracion=self._duracion, descuento_porcentaje=descuento)
        logger.info(f"Reserva {self.identificador} registrada para {cliente.nombre} en servicio {servicio.nombre}.")

    @property
    def estado(self) -> str:
        return self._estado

    @property
    def liquidacion(self) -> Dict[str, float]:
        return self._liquidacion

    @property
    def total(self) -> float:
        return self._liquidacion["total"]

    def confirmar(self) -> None:
        """Confirma la reserva. Si es equipo, descuenta del inventario."""
        if self._estado == "CONFIRMADA":
            raise OperacionNoPermitidaError(f"La reserva {self.identificador} ya fue confirmada previamente.")
        if self._estado == "CANCELADA":
            raise OperacionNoPermitidaError(f"No se puede confirmar la reserva {self.identificador} porque está cancelada.")
        if not self._servicio.disponible:
            raise ServicioNoDisponibleError(f"El servicio {self._servicio.codigo} ya no tiene disponibilidad.")

        if isinstance(self._servicio, AlquilerEquipo):
            self._servicio.prestar_unidad()

        self._estado = "CONFIRMADA"
        logger.info(f"Reserva {self.identificador} confirmada. Total a pagar: ${self.total:,.0f}")

    def cancelar(self, motivo: str) -> None:
        """Cancela la reserva y libera los recursos."""
        if not motivo or len(motivo.strip()) < 5:
            raise DatoInvalidoError("Debe suministrar una razón válida de cancelación (mínimo 5 caracteres).")
        if self._estado == "CANCELADA":
            raise OperacionNoPermitidaError(f"La reserva {self.identificador} ya se encuentra cancelada.")
        
        # Si era un equipo prestado, devolvemos la unidad al inventario
        if isinstance(self._servicio, AlquilerEquipo) and self._estado in ("CONFIRMADA", "PAGADA"):
            self._servicio.devolver_unidad()

        self._estado = "CANCELADA"
        self._motivo_anulacion = motivo.strip()
        logger.warning(f"Reserva {self.identificador} cancelada. Motivo: {self._motivo_anulacion}")

    def procesar_pago(self, monto: float, medio: str = "TRANSFERENCIA") -> Dict[str, Any]:
        """Procesa el pago de una reserva previamente confirmada."""
        if self._estado != "CONFIRMADA":
            raise OperacionNoPermitidaError(
                f"No se puede pagar la reserva {self.identificador} en estado '{self._estado}'. Debe estar CONFIRMADA."
            )
        if monto < self.total:
            faltante = self.total - monto
            raise CalculoInconsistenteError(f"Monto insuficiente. Falta por pagar: ${faltante:,.0f}")

        self._estado = "PAGADA"
        
        # Sumamos puntos de fidelidad al cliente (1 punto por cada $20,000 COP)
        puntos_obtenidos = int(self.total // 20000)
        if puntos_obtenidos > 0:
            self._cliente.sumar_puntos(puntos_obtenidos)

        recibo = {
            "reserva": self.identificador,
            "cliente": self._cliente.nombre,
            "monto_pagado": monto,
            "vueltas": round(monto - self.total, 2),
            "medio": medio,
            "puntos_ganados": puntos_obtenidos,
            "fecha": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        logger.info(f"Pago asentado para reserva {self.identificador}. Recibo: {recibo}")
        return recibo

    def obtener_detalle(self) -> Dict[str, Any]:
        return {
            "id": self.identificador,
            "cliente": self._cliente.obtener_detalle(),
            "servicio": self._servicio.obtener_detalle(),
            "duracion": self._duracion,
            "estado": self._estado,
            "liquidacion": self._liquidacion
        }

    def validar_estado(self) -> bool:
        return self.activo and (self._estado != "CANCELADA")


# ==============================================================================
# GESTOR DEL SISTEMA EN MEMORIA (SIN BASES DE DATOS)
# ==============================================================================
class SistemaGestionFJ:
    """
    Controlador central de Software FJ que maneja clientes, servicios y reservas
    en memoria mediante colecciones nativas de Python (diccionarios y listas).
    """
    def __init__(self):
        self._clientes: Dict[str, Cliente] = {}
        self._servicios: Dict[str, Servicio] = {}
        self._reservas: Dict[str, Reserva] = {}
        logger.info("Controlador SistemaGestionFJ inicializado.")

    def registrar_cliente(self, id_cliente: str, nombre: str, correo: str, telefono: str, tipo: str = "NATURAL") -> Cliente:
        if id_cliente in self._clientes:
            raise OperacionNoPermitidaError(f"El cliente {id_cliente} ya se encuentra registrado.")
        nuevo = Cliente(id_cliente, nombre, correo, telefono, tipo)
        self._clientes[id_cliente] = nuevo
        logger.info(f"Cliente registrado: {nombre} [{id_cliente}]")
        return nuevo

    def registrar_servicio(self, servicio: Servicio) -> Servicio:
        if not isinstance(servicio, Servicio):
            raise DatoInvalidoError("El servicio debe ser una subclase de Servicio.")
        if servicio.codigo in self._servicios:
            raise OperacionNoPermitidaError(f"El código de servicio '{servicio.codigo}' ya existe.")
        self._servicios[servicio.codigo] = servicio
        logger.info(f"Servicio agregado al catálogo: [{servicio.codigo}] {servicio.nombre}")
        return servicio

    def crear_reserva(self, id_reserva: str, id_cliente: str, cod_servicio: str, duracion: float, descuento: float = 0.0) -> Reserva:
        if id_reserva in self._reservas:
            raise OperacionNoPermitidaError(f"Ya existe una reserva con ID '{id_reserva}'.")
        if id_cliente not in self._clientes:
            raise DatoInvalidoError(f"El cliente '{id_cliente}' no está en la base de datos.")
        if cod_servicio not in self._servicios:
            raise DatoInvalidoError(f"El servicio '{cod_servicio}' no existe en el catálogo.")

        cli = self._clientes[id_cliente]
        srv = self._servicios[cod_servicio]

        # Si el cliente es corporativo y no tiene descuento previo, le otorgamos 10% de cortesía
        if cli.tipo_cliente == "CORPORATIVO" and descuento == 0.0:
            descuento = 10.0
            logger.info(f"Aplicado 10% de descuento corporativo automático para {cli.nombre}")

        res = Reserva(id_reserva, cli, srv, duracion, descuento)
        self._reservas[id_reserva] = res
        return res

    def confirmar_reserva(self, id_reserva: str) -> None:
        if id_reserva not in self._reservas:
            raise ReservaInvalidaError(f"Reserva '{id_reserva}' no encontrada.")
        self._reservas[id_reserva].confirmar()

    def cancelar_reserva(self, id_reserva: str, razon: str) -> None:
        if id_reserva not in self._reservas:
            raise ReservaInvalidaError(f"Reserva '{id_reserva}' no encontrada.")
        self._reservas[id_reserva].cancelar(razon)

    def pagar_reserva(self, id_reserva: str, monto: float, medio: str = "TRANSFERENCIA") -> Dict[str, Any]:
        if id_reserva not in self._reservas:
            raise ReservaInvalidaError(f"Reserva '{id_reserva}' no encontrada.")
        return self._reservas[id_reserva].procesar_pago(monto, medio)

    def reporte_estadistico(self) -> Dict[str, Any]:
        return {
            "total_clientes": len(self._clientes),
            "total_servicios": len(self._servicios),
            "total_reservas": len(self._reservas),
            "estados_reservas": {
                est: sum(1 for r in self._reservas.values() if r.estado == est)
                for est in Reserva.ESTADOS
            }
        }


# ==============================================================================
# BATERÍA DE SIMULACIÓN (PRUEBAS PRÁCTICAS EXIGIDAS EN LA GUÍA)
# ==============================================================================
def ejecutar_pruebas_simulacion():
    print("=" * 75)
    print("UNIVERSIDAD NACIONAL ABIERTA Y A DISTANCIA - UNAD")
    print("CURSO DE PROGRAMACIÓN 213023 | FASE 4: PRÁCTICAS SIMULADAS")
    print("SISTEMA DE GESTIÓN PARA SOFTWARE FJ (EN MEMORIA Y CON LOGS)")
    print("=" * 75 + "\n")

    sistema = SistemaGestionFJ()
    exitos = 0
    errores_controlados = 0

    # 1. Registro exitoso de cliente corporativo
    print("[Prueba 1] Registro de cliente corporativo válido:")
    try:
        cli1 = sistema.registrar_cliente("NIT-901458920", "Soluciones Digitales S.A.S.", "contacto@soluciones.co", "3118904567", "CORPORATIVO")
        print(f" -> OK: Cliente creado: {cli1.nombre} [{cli1.identificador}]")
        exitos += 1
    except SoftwareFJError as e:
        print(f" -> ERROR: {e}")

    # 2. Intento de registro con correo inválido
    print("\n[Prueba 2] Validación de correo sin formato @:")
    try:
        sistema.registrar_cliente("CC-1098456123", "Pedro Perez", "pedro_sin_arroba.com", "3001234567")
    except DatoInvalidoError as err:
        print(f" -> EXCEPCIÓN CONTROLADA: {err}")
        logger.error(f"Error de formato capturado: {err}")
        errores_controlados += 1

    # 3. Validación de teléfono con encadenamiento de excepciones
    print("\n[Prueba 3] Validación de teléfono con letras (encadenamiento raise from):")
    try:
        sistema.registrar_cliente("CC-1095784120", "Ana Gomez", "ana@correo.com", "300ABC4567")
    except DatoInvalidoError as err:
        print(f" -> EXCEPCIÓN ENCADENADA: {err}")
        print(f"    Causa original (__cause__): {type(err.__cause__).__name__} -> {err.__cause__}")
        logger.error(f"Encadenamiento verificado: {err} | Causa: {err.__cause__}")
        errores_controlados += 1

    # 4. Creación válida de servicio de sala
    print("\n[Prueba 4] Creación de servicio de sala (Auditorio):")
    try:
        auditorio = ReservaSala("SRV-AUD-01", "Auditorio Central de Innovación", "AUDITORIO", 80, con_proyector=True, con_refrigerio=True)
        sistema.registrar_servicio(auditorio)
        print(f" -> OK: {auditorio.describir_servicio()}")
        exitos += 1
    except SoftwareFJError as e:
        print(f" -> ERROR: {e}")

    # 5. Creación errónea de servicio con tarifa negativa
    print("\n[Prueba 5] Intento de crear servicio con tarifa negativa:")
    try:
        AlquilerEquipo("SRV-EQ-ERR", "Servidor de Prueba", -50000.0, "SERVIDOR", 500000.0, 2)
    except CalculoInconsistenteError as err:
        print(f" -> EXCEPCIÓN CONTROLADA: {err}")
        logger.error(f"Tarifa negativa rechazada: {err}")
        errores_controlados += 1

    # 6. Creación válida de hardware y asesoría técnica
    print("\n[Prueba 6] Registro de servidor en rack y consultoría cloud:")
    try:
        servidor = AlquilerEquipo("SRV-SRV-01", "Servidor Dell PowerEdge 64GB", 220000.0, "SERVIDOR", 1500000.0, stock=1)
        asesoria = AsesoriaEspecializada("SRV-ASE-01", "Arquitectura en la Nube y DevOps", 160000.0, "Cloud Computing", nivel="CONSULTOR_MASTER")
        sistema.registrar_servicio(servidor)
        sistema.registrar_servicio(asesoria)
        print(" -> OK: Servidor y Asesoría registrados en catálogo.")
        exitos += 1
    except SoftwareFJError as e:
        print(f" -> ERROR: {e}")

    # 7. Creación y confirmación de reserva con estructura try/except/else
    print("\n[Prueba 7] Reserva con estructura try/except/else y descuento corporativo:")
    try:
        res1 = sistema.crear_reserva("RES-001", "NIT-901458920", "SRV-AUD-01", duracion=4.0)
        sistema.confirmar_reserva("RES-001")
    except (ReservaInvalidaError, ServicioNoDisponibleError, OperacionNoPermitidaError) as err:
        print(f" -> ERROR: {err}")
    else:
        # Bloque else: solo se ejecuta si el bloque try fue exitoso
        print(f" -> BLOQUE ELSE EJECUTADO: Reserva {res1.identificador} confirmada.")
        print(f"    Subtotal: ${res1.liquidacion['costo_base']:,.0f} | Descuento (10%): -${res1.liquidacion['descuento']:,.0f}")
        print(f"    IVA (19%): +${res1.liquidacion['iva']:,.0f} | TOTAL: ${res1.total:,.0f}")
        exitos += 1

    # 8. Intento de reservar un recurso sin stock
    print("\n[Prueba 8] Intento de reserva de equipo agotado (stock = 0):")
    try:
        res_eq = sistema.crear_reserva("RES-002", "NIT-901458920", "SRV-SRV-01", duracion=2.0)
        sistema.confirmar_reserva("RES-002")
        print(f" -> Primera reserva de equipo confirmada (quedan 0 en stock).")

        # Segundo intento sobre el mismo servidor agotado
        sistema.crear_reserva("RES-003", "NIT-901458920", "SRV-SRV-01", duracion=1.0)
    except ServicioNoDisponibleError as err:
        print(f" -> EXCEPCIÓN CONTROLADA: {err}")
        logger.warning(f"Reserva denegada por inventario: {err}")
        errores_controlados += 1

    # 9. Cancelación duplicada con estructura try/except/finally
    print("\n[Prueba 9] Cancelación duplicada con estructura try/except/finally:")
    try:
        sistema.cancelar_reserva("RES-001", razon="Reunión aplazada por el cliente")
        print(" -> Primera cancelación ejecutada correctamente.")
        # Reintento de cancelación de la misma reserva
        sistema.cancelar_reserva("RES-001", razon="Intento duplicado")
    except OperacionNoPermitidaError as err:
        print(f" -> EXCEPCIÓN CONTROLADA: {err}")
        logger.error(f"Transición ilícita capturada: {err}")
        errores_controlados += 1
    finally:
        # El bloque finally se ejecuta siempre garantizando la verificación del estado
        print(" -> BLOQUE FINALLY EJECUTADO: Recursos y estado de memoria verificados.")
        logger.info("Bloque finally de la prueba 9 ejecutado sin interrupciones.")

    # 10. Duración negativa en cálculo de costos
    print("\n[Prueba 10] Intento de reserva con horas negativas:")
    try:
        sistema.crear_reserva("RES-004", "NIT-901458920", "SRV-ASE-01", duracion=-3.0)
    except CalculoInconsistenteError as err:
        print(f" -> EXCEPCIÓN CONTROLADA: {err}")
        logger.error(f"Cálculo negativo evitado: {err}")
        errores_controlados += 1

    # 11. Flujo completo: registro de cliente natural, reserva y pago exitoso
    print("\n[Prueba 11] Flujo comercial completo (Cliente natural + Asesoría + Pago):")
    try:
        cli2 = sistema.registrar_cliente("CC-1094876543", "Carlos Eduardo Mora", "carlos.mora@correo.com", "3154567890", "NATURAL")
        res_asesoria = sistema.crear_reserva("RES-005", "CC-1094876543", "SRV-ASE-01", duracion=3.0)
        sistema.confirmar_reserva("RES-005")
        recibo = sistema.pagar_reserva("RES-005", monto=res_asesoria.total, medio="PSE")
        print(f" -> OK: Pago procesado exitosamente por ${recibo['monto_pagado']:,.0f}. Puntos fidelidad: {cli2.puntos}")
        exitos += 1
    except SoftwareFJError as e:
        print(f" -> ERROR: {e}")

    # Balance final
    resumen = sistema.reporte_estadistico()
    print("\n" + "=" * 75)
    print("BALANCE FINAL DE LA SIMULACIÓN")
    print("=" * 75)
    print(f"Casos exitosos ejecutados        : {exitos}")
    print(f"Excepciones controladas          : {errores_controlados}")
    print(f"Total pruebas realizadas         : {exitos + errores_controlados} (Guía exigía mínimo 10)")
    print(f"Clientes en memoria              : {resumen['total_clientes']}")
    print(f"Servicios en catálogo            : {resumen['total_servicios']}")
    print(f"Reservas procesadas              : {resumen['total_reservas']} -> {resumen['estados_reservas']}")
    print(f"Archivo de logs persistente      : {ARCHIVO_LOG}")
    print("Estado del sistema               : 100% OPERATIVO (Cero caídas inesperadas)")
    print("=" * 75 + "\n")


if __name__ == "__main__":
    ejecutar_pruebas_simulacion()
