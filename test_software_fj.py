# -*- coding: utf-8 -*-
"""
Pruebas Unitarias Automatizadas con Pytest
Curso de Programación 213023 - UNAD
Estudiante: Janner Jose Vega Torres
"""

import pytest
from software_fj import (
    Cliente,
    ReservaSala,
    AlquilerEquipo,
    AsesoriaEspecializada,
    SistemaGestionFJ,
    DatoInvalidoError,
    ServicioNoDisponibleError,
    OperacionNoPermitidaError,
    CalculoInconsistenteError
)


class TestCliente:
    """Pruebas de validación y encapsulamiento en la clase Cliente."""

    def test_cliente_valido(self):
        c = Cliente("CC-1098123456", "Juan David Gomez", "juan.gomez@correo.com", "3001234567", "NATURAL")
        assert c.nombre == "Juan David Gomez"
        assert c.correo == "juan.gomez@correo.com"
        assert c.telefono == "3001234567"
        assert c.validar_estado() is True

    def test_correo_sin_formato_falla(self):
        with pytest.raises(DatoInvalidoError) as exc_info:
            Cliente("CC-1098123456", "Juan Gomez", "correo_sin_arroba.com", "3001234567")
        assert "no tiene un formato válido" in str(exc_info.value)

    def test_telefono_con_letras_encadena_error(self):
        with pytest.raises(DatoInvalidoError) as exc_info:
            Cliente("CC-1098123456", "Juan Gomez", "juan@correo.com", "300ABC4567")
        assert "letras o símbolos" in str(exc_info.value)
        # Verificamos que la causa original guardada en __cause__ sea un ValueError
        assert isinstance(exc_info.value.__cause__, ValueError)

    def test_telefono_longitud_incorrecta(self):
        with pytest.raises(DatoInvalidoError) as exc_info:
            Cliente("CC-1098123456", "Juan Gomez", "juan@correo.com", "300123")
        assert "exactamente 10 dígitos" in str(exc_info.value)


class TestServicios:
    """Pruebas de polimorfismo y sobrecarga en los servicios."""

    def test_reserva_sala_calculo_costos(self):
        # 3 horas en sala de juntas: 3 * 50,000 = 150,000 + 30,000 (proyector) = 180,000
        sala = ReservaSala("SALA-01", "Sala Estrategia", "JUNTAS", 10, con_proyector=True, con_refrigerio=False)
        assert sala.calcular_costo_base(3.0) == 180000.0

        # Liquidación con 10% de descuento e IVA del 19%
        liq = sala.liquidar_costo(duracion=3.0, descuento_porcentaje=10.0, iva_porcentaje=0.19)
        assert liq["costo_base"] == 180000.0
        assert liq["descuento"] == 18000.0
        assert liq["base_gravable"] == 162000.0
        assert liq["iva"] == 30780.0
        assert liq["total"] == 192780.0

    def test_alquiler_equipo_control_stock(self):
        servidor = AlquilerEquipo("EQ-01", "Servidor Local", 100000.0, "SERVIDOR", 500000.0, stock=1)
        assert servidor.disponible is True
        servidor.prestar_unidad()
        assert servidor.stock == 0
        assert servidor.disponible is False

        # Intentar prestar cuando ya no hay stock
        with pytest.raises(ServicioNoDisponibleError):
            servidor.prestar_unidad()

    def test_asesoria_minimo_dos_horas(self):
        asesoria = AsesoriaEspecializada("ASE-01", "Auditoría TI", 120000.0, "Ciberseguridad")
        with pytest.raises(CalculoInconsistenteError):
            asesoria.calcular_costo_base(1.0)


class TestCicloReservas:
    """Pruebas de estados y transiciones en reservas."""

    @pytest.fixture
    def sistema_configurado(self):
        s = SistemaGestionFJ()
        s.registrar_cliente("NIT-900111222", "Tech Corp S.A.", "tech@corp.com", "3109876543", "CORPORATIVO")
        s.registrar_servicio(ReservaSala("SALA-AUD", "Auditorio Principal", "AUDITORIO", 50))
        return s

    def test_flujo_reserva_confirmada_y_pagada(self, sistema_configurado):
        s = sistema_configurado
        res = s.crear_reserva("RES-100", "NIT-900111222", "SALA-AUD", duracion=2.0)
        assert res.estado == "REGISTRADA"

        s.confirmar_reserva("RES-100")
        assert res.estado == "CONFIRMADA"

        recibo = s.pagar_reserva("RES-100", monto=res.total)
        assert recibo["reserva"] == "RES-100"
        assert res.estado == "PAGADA"

    def test_cancelacion_duplicada_lanza_excepcion(self, sistema_configurado):
        s = sistema_configurado
        res = s.crear_reserva("RES-200", "NIT-900111222", "SALA-AUD", duracion=2.0)
        s.cancelar_reserva("RES-200", razon="Cancelación justificada")
        assert res.estado == "CANCELADA"

        with pytest.raises(OperacionNoPermitidaError):
            s.cancelar_reserva("RES-200", razon="Intento duplicado de cancelar")
