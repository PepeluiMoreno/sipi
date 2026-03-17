// src/mocks/index.js
export const mockInmuebles = [
  { 
    id: '1', lat: 40.4168, lng: -3.7038, 
    direccion: 'Calle Mayor 123', localidad: 'Madrid', provincia: 'Madrid', 
    estado: 'No investigado', localidadId: '111', 
    denominacion_principal: 'Iglesia de San Miguel', 
    direccion_normalizada: 'Calle Mayor, 123', 
    es_bic: false, enVenta: false, vendido: false,
    photo: 'https://images.unsplash.com/photo-1502005229762-cf9565b9ebea?w=400&h=300&fit=crop' 
  },
  { 
    id: '2', lat: 40.4180, lng: -3.7050, 
    direccion: 'Gran Vía 45', localidad: 'Madrid', provincia: 'Madrid', 
    estado: 'Inmatriculado', localidadId: '111', 
    denominacion_principal: 'Catedral de la Almudena', 
    direccion_normalizada: 'Gran Vía, 45', 
    es_bic: true, enVenta: false, vendido: false,
    photo: 'https://images.unsplash.com/photo-1503315082122-21e2e37b8f7c?w=400&h=300&fit=crop' 
  },
  { 
    id: '3', lat: 40.4175, lng: -3.7042, 
    direccion: 'Plaza Mayor 1', localidad: 'Madrid', provincia: 'Madrid', 
    estado: 'En venta', localidadId: '111', 
    denominacion_principal: 'Convento de las Descalzas', 
    direccion_normalizada: 'Plaza Mayor, 1', 
    es_bic: false, enVenta: true, vendido: false,
    photo: 'https://images.unsplash.com/photo-1513584684374-8bab748fbf90?w=400&h=300&fit=crop' 
  },
  { 
    id: '4', lat: 41.3851, lng: 2.1734, 
    direccion: 'Paseo de Gracia 43', localidad: 'Barcelona', provincia: 'Barcelona', 
    estado: 'Inmatriculado', localidadId: '222', 
    denominacion_principal: 'Casa Batlló', 
    direccion_normalizada: 'Paseo de Gracia, 43', 
    es_bic: true, enVenta: false, vendido: false,
    photo: 'https://images.unsplash.com/photo-1583422409516-2895a77efded?w=400&h=300&fit=crop' 
  },
  { 
    id: '5', lat: 41.4036, lng: 2.1744, 
    direccion: 'Carrer de Mallorca 401', localidad: 'Barcelona', provincia: 'Barcelona', 
    estado: 'Vendido', localidadId: '222', 
    denominacion_principal: 'Sagrada Familia', 
    direccion_normalizada: 'Carrer de Mallorca, 401', 
    es_bic: true, enVenta: false, vendido: true,
    photo: 'https://images.unsplash.com/photo-1589182373726-e4f658ab50f0?w=400&h=300&fit=crop' 
  },
  // Agregar más inmuebles para mejor testing
  { 
    id: '6', lat: 40.4238, lng: -3.6991, 
    direccion: 'Calle de Alcalá 52', localidad: 'Madrid', provincia: 'Madrid', 
    estado: 'No investigado', localidadId: '111', 
    denominacion_principal: 'Palacio de Cibeles', 
    direccion_normalizada: 'Calle de Alcalá, 52', 
    es_bic: true, enVenta: false, vendido: false,
    photo: 'https://images.unsplash.com/photo-1541336032412-2048a678540d?w=400&h=300&fit=crop' 
  },
  { 
    id: '7', lat: 41.6488, lng: -0.8891, 
    direccion: 'Plaza del Pilar 1', localidad: 'Zaragoza', provincia: 'Zaragoza', 
    estado: 'Inmatriculado', localidadId: '333', 
    denominacion_principal: 'Basílica del Pilar', 
    direccion_normalizada: 'Plaza del Pilar, 1', 
    es_bic: true, enVenta: false, vendido: false,
    photo: 'https://images.unsplash.com/photo-1592409065737-a253f290c440?w=400&h=300&fit=crop' 
  },
  { 
    id: '8', lat: 37.3891, lng: -5.9845, 
    direccion: 'Avenida de la Constitución', localidad: 'Sevilla', provincia: 'Sevilla', 
    estado: 'En venta', localidadId: '444', 
    denominacion_principal: 'Catedral de Sevilla', 
    direccion_normalizada: 'Avenida de la Constitución, s/n', 
    es_bic: true, enVenta: true, vendido: false,
    photo: 'https://images.unsplash.com/photo-1556800573-5678a77d493a?w=400&h=300&fit=crop' 
  },
  { 
    id: '9', lat: 39.8628, lng: -4.0273, 
    direccion: 'Calle Alfonso X', localidad: 'Toledo', provincia: 'Toledo', 
    estado: 'Vendido', localidadId: '555', 
    denominacion_principal: 'Sinagoga del Tránsito', 
    direccion_normalizada: 'Calle Alfonso X, 4', 
    es_bic: true, enVenta: false, vendido: true,
    photo: 'https://images.unsplash.com/photo-1577717903315-1691ae25ab3f?w=400&h=300&fit=crop' 
  },
  { 
    id: '10', lat: 42.8782, lng: -8.5448, 
    direccion: 'Praza do Obradoiro', localidad: 'Santiago de Compostela', provincia: 'A Coruña', 
    estado: 'No investigado', localidadId: '666', 
    denominacion_principal: 'Catedral de Santiago', 
    direccion_normalizada: 'Praza do Obradoiro, 1', 
    es_bic: true, enVenta: false, vendido: false,
    photo: 'https://images.unsplash.com/photo-1589977901212-1d4ae8f72e2a?w=400&h=300&fit=crop' 
  }
]

export const ESTADO_MAPEO = {
  'No investigado': 'no_investigado',
  'Inmatriculado': 'inmatriculado',
  'Vendido': 'vendido',
  'En venta': 'en_venta',
  'BIC': 'bic'
}