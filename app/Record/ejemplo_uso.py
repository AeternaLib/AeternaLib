from historial import Historial

historial = Historial()
# Ejecutar solo DESPUÉS de que el módulo de préstamos confirme la operación.
historial.registrar_prestamo('usuario-01', 'libro-03', 'prestamo-100')
historial.registrar_devolucion('usuario-01', 'libro-03', 'prestamo-100')
for movimiento in historial.consultar(usuario_id='usuario-01'):
    print(movimiento)
