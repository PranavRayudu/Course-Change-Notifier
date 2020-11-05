// middleware functions
export function fetchLoginData(success, fail) {
    return function (dispatch) {
        dispatch(requestLoginData())
        return fetch(`/api/v1/login_status`, {
            method: 'GET',
        }).then(res => {
            if (!res.ok) throw new Error()
            return res.json()
        }).then(data => {
            if (success) success()
            dispatch(receiveLoginData(data))
        }).catch((err) => {
            if (fail) fail()
            dispatch(receiveLoginData())
        })
    }
}

export function postUserLogin(data, success, fail) {
    return function (dispatch) {
        dispatch(requestUserLogin())
        fetch(`/login`, {
            method: 'POST',
            body: data,
        }).then(res => {
            if (!res.ok) throw new Error()
            return res.json()
        }).then((data) => {
            if (data.user && success) success()
            if (!data.user && fail) fail()
            dispatch(receiveLoginData(data))
        }).catch((err) => {
            if (fail) fail()
            dispatch(receiveLoginData())
        })
    }
}

export function postBrowserLogin(success, fail) {
    return function (dispatch) {
        dispatch(requestBrowserLogin())
        fetch(`/api/v1/browser_login`, {
            method: 'POST',
        }).then(res => {
            if (!res.ok) throw new Error()
            return res.json()
        }).then(data => {
            if (data.browser && success) success()
            if (!data.browser && fail) fail()
            dispatch(receiveLoginData(data))
            fetchCourseData()
        }).catch((err) => {
            if (fail) fail()
            dispatch(receiveLoginData())
        })
    }
}


// actions
export const GET_LOGIN = '/login/GET_LOGIN'  // get login data from server
function requestLoginData() {
    return {type: GET_LOGIN}
}

export const REQUEST_USER_LOGIN = '/login/USER_LOGIN'  // send login data to server
function requestUserLogin() {
    return {type: REQUEST_USER_LOGIN}
}

export const REQUEST_BROWSER_LOGIN = '/login/BROWSER_LOGIN'  // send browser login request to server
function requestBrowserLogin() {
    return {type: REQUEST_BROWSER_LOGIN}
}

export const SET_LOGIN = '/login/SET_LOGIN'  // set login data in state
function receiveLoginData(payload) {
    return {type: SET_LOGIN, payload}
}


// middleware functions
export function fetchConfigData(success, fail) {
    return function (dispatch) {
        fetch('/api/v1/config').then((res) => {
            if (!res.ok) throw new Error()
            return res.json()
        }).then((data) => {
            if (success) success()
            dispatch(receiveConfigData(data))
        }).catch(() => {
            if (fail) fail()
        })
    }
}

export function postConfigData({interval, timeRange}, success, fail) {
    return function (dispatch, getState) {
        const {interval: curInterval, timeRange: curTimeRange} = getState()
        let send_dict = {}

        if (curInterval !== interval) {
            send_dict['interval'] = interval
        }

        if (curTimeRange !== timeRange) {
            if (timeRange && timeRange[0] && timeRange[1]) {
                send_dict['start'] = timeRange[0].format('HHmm')
                send_dict['end'] = timeRange[1].format('HHmm')
            } else {
                send_dict['start'] = 'none'
                send_dict['end'] = 'none'
            }
        }

        if (!isEmpty(send_dict)) { // will not be empty
            sendConfigData(send_dict, dispatch, success, fail)
        }
    }
}

function sendConfigData(config, dispatch, success, fail) {
    fetch('/api/v1/config?' + serialize(config), {
        method: 'POST',
    }).then((res) => {
        if (!res.ok) throw new Error()
        return res.json()
    }).then((data) => {
        if (success) success()
        dispatch(receiveConfigData(data))
    }).catch(() => {
        if (fail) fail()
    })
}


// actions
export const SET_CONFIG = 'SET_CONFIG'

function receiveConfigData(payload) {
    return {type: SET_CONFIG, payload}
}


// middleware functions

export function fetchCourseData(success, fail) {
    return function (dispatch) {
        dispatch(startCourseRequest())
        fetch(`/api/v1/courses`, {}).then(res => {
            if (!res.ok) throw new Error()
            return res.json()
        }).then(data => {
            if (success) success()
            dispatch(receiveCourseData(data))
        }).catch((err) => {
            if (fail) fail()
            dispatch(receiveCourseDataFail())
        })
    }
}

export function postCourse(uid, data, success, fail) {
    return function (dispatch) {
        dispatch(startCourseRequest())
        fetch(`/api/v1/courses/${uid}?` + serialize(data), {
            method: 'POST'
        }).then((res) => {
            if (!res.ok) throw new Error()
            return res.json()
        }).then((data) => {
            if (success) success()
            dispatch(updateCourse(data))
        }).catch((err) => {
            if (fail) fail()
            dispatch(receiveCourseDataFail())
        })
    }
}

export function unpostCourses(courses, success, fail) {
    return function (dispatch) {
        dispatch(startCourseRequest())
        let fetches = []
        courses.forEach(course => {
            fetches.push(fetch(`/api/v1/courses/${course.uid}`, {
                method: 'DELETE',
            }))
        })

        Promise.all(fetches).then(async (res) => {
            return Promise.all(res.map(r => r.json()))
        }).then((data) => {
            if (success) success()
            dispatch(removeCourses(data))
        }).catch((err) => {
            if (fail) fail()
            dispatch(receiveCourseDataFail())
            dispatch(fetchCourseData()) // take care of partial success
        })
    }
}

// actions

export const GET_COURSES = 'courses/GET_COURSES'

function startCourseRequest() {
    return {type: GET_COURSES}
}

export const SET_COURSES = 'courses/SET_COURSES'  // set login data in state
function receiveCourseData(payload) {
    return {type: SET_COURSES, payload}
}

function receiveCourseDataFail() {
    return {type: SET_COURSES, status: 'fail'}
}

export const UPDATE_COURSE = 'courses/ADD_COURSE' // also counts as update

function updateCourse(payload) {
    return {type: UPDATE_COURSE, payload}
}

export const REMOVE_COURSES = 'courses/REMOVE_COURSES'

function removeCourses(payload) {
    return {type: REMOVE_COURSES, payload}
}


// helper functions
function isEmpty(obj) {
    return Object.keys(obj).length === 0
}

function serialize(obj = {}) {
    const str = [];
    for (let p in obj)
        if (obj.hasOwnProperty(p)) {
            str.push(encodeURIComponent(p) + "=" + encodeURIComponent(obj[p]));
        }
    return str.join("&");
}
