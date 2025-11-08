"use client"

import React, { createContext, useContext, useReducer } from 'react'

// Action types
const SHOW_ERROR = 'SHOW_ERROR'
const HIDE_ERROR = 'HIDE_ERROR'

// Reducer
const errorReducer = (state, action) => {
  switch (action.type) {
    case SHOW_ERROR:
      return {
        ...state,
        isVisible: true,
        title: action.payload?.title || 'Error',
        message: action.payload?.message || 'Something went wrong',
        onRetry: action.payload?.onRetry || null
      }
    case HIDE_ERROR:
      return {
        ...state,
        isVisible: false,
        title: 'Error',
        message: '',
        onRetry: null
      }
    default:
      return state
  }
}

// Initial state
const initialState = {
  isVisible: false,
  title: 'Error',
  message: '',
  onRetry: null
}

// Context
const ErrorDialogContext = createContext(null)

// Provider
export const ErrorDialogProvider = ({ children }) => {
  const [state, dispatch] = useReducer(errorReducer, initialState)

  const actions = {
    showError: (payload) => dispatch({ type: SHOW_ERROR, payload }),
    hideError: () => dispatch({ type: HIDE_ERROR })
  }

  return (
    <ErrorDialogContext.Provider value={{ ...state, ...actions }}>
      {children}
    </ErrorDialogContext.Provider>
  )
}

// Hook
export const useErrorDialog = () => {
  const context = useContext(ErrorDialogContext)
  if (!context) {
    throw new Error('useErrorDialog must be used within an ErrorDialogProvider')
  }
  return context
}
