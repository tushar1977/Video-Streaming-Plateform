// context/LoaderContext.js
"use client"

import React, { createContext, useContext, useReducer } from 'react'

// Action types
const SHOW_LOADER = 'SHOW_LOADER'
const HIDE_LOADER = 'HIDE_LOADER'

// Reducer
const loaderReducer = (state, action) => {
  switch (action.type) {
    case SHOW_LOADER:
      return {
        ...state,
        isLoading: true,
        message: action.payload?.message || 'Loading...'
      }
    case HIDE_LOADER:
      return {
        ...state,
        isLoading: false,
        message: ''
      }
    default:
      return state
  }
}

// Initial state
const initialState = {
  isLoading: false,
  message: 'Loading...'
}

// Context
const LoaderContext = createContext(null)

// Provider
export const LoaderProvider = ({ children }) => {
  const [state, dispatch] = useReducer(loaderReducer, initialState)

  const actions = {
    showLoader: (message) => dispatch({ type: SHOW_LOADER, payload: { message } }),
    hideLoader: () => dispatch({ type: HIDE_LOADER })
  }

  return (
    <LoaderContext.Provider value={{ ...state, ...actions }}>
      {children}
    </LoaderContext.Provider>
  )
}

// Hook
export const useLoader = () => {
  const context = useContext(LoaderContext)
  if (!context) {
    throw new Error('useLoader must be used within a LoaderProvider')
  }
  return context
}
